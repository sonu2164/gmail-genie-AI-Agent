import base64
import re
import os
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timedelta

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.readonly', 
    'https://www.googleapis.com/auth/gmail.metadata'
]

def gmail_authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def categorize_email(subject, sender):
    """Categorize email based on subject and sender"""
    promotions_keywords = ['sale', 'discount', 'offer', 'promo']
    social_keywords = ['linkedin', 'twitter', 'facebook', 'instagram']
    
    if any(keyword in subject.lower() for keyword in promotions_keywords):
        return 'Promotions'
    elif any(keyword in sender.lower() for keyword in social_keywords):
        return 'Social'
    elif 'notification' in subject.lower() or 'update' in subject.lower():
        return 'Updates'
    else:
        return 'Primary'

def advanced_categorization(subject, sender, body=None):
    """Enhanced categorization using NLP techniques and more categories"""
    # Add more categories like Finance, Travel, Shopping, Work, Personal, etc.
    # Use regex patterns or NLP libraries for better classification
    finance_patterns = ['invoice', 'payment', 'receipt', 'transaction', 'bank', 'credit']
    travel_patterns = ['flight', 'booking', 'reservation', 'hotel', 'itinerary', 'travel']
    shopping_patterns = ['order', 'shipped', 'delivery', 'tracking', 'purchase']
    
    # Check body content if available for better categorization
    content_to_check = (body or '') + subject.lower() + sender.lower()
    
    if any(pattern in content_to_check for pattern in finance_patterns):
        return 'Finance'
    elif any(pattern in content_to_check for pattern in travel_patterns):
        return 'Travel'
    elif any(pattern in content_to_check for pattern in shopping_patterns):
        return 'Shopping'
    # Fall back to existing categories
    return categorize_email(subject, sender)

def get_unsubscribe_link(service, msg_id):
    """Extract unsubscribe link from email headers or body with priority to 'Unsubscribe' text links"""
    try:
        # First try to get it from email body with "Unsubscribe" text
        full_msg = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()


     
        
        # Extract body
        body = ""
        if 'parts' in full_msg['payload']:
            for part in full_msg['payload']['parts']:
                if part['mimeType'] == 'text/html':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/plain' and not body:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        elif 'body' in full_msg['payload'] and 'data' in full_msg['payload']['body']:
            body = base64.urlsafe_b64decode(full_msg['payload']['body']['data']).decode('utf-8')
        
        if body:
            # Priority 1: Find links with "Unsubscribe" text
            unsubscribe_link = re.search(
                r'<a\s+[^>]*href=["\'](https?://[^>]+)["\'][^>]*>.*?Unsubscribe.*?</a>',
                body,
                re.IGNORECASE
            )
            if unsubscribe_link:
                return unsubscribe_link.group(1)

        # Priority 2: Check standard List-Unsubscribe header
        msg_data = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='metadata',
            metadataHeaders=['List-Unsubscribe', 'List-Unsubscribe-Post']
        ).execute()
        
        headers = msg_data['payload']['headers']
        unsubscribe = next((h['value'] for h in headers if h['name'].lower() == 'list-unsubscribe'), None)
        
        if unsubscribe:
            url_match = re.search(r'<(https?://[^>]+)>', unsubscribe)
            if url_match:
                return url_match.group(1)
            mailto_match = re.search(r'<mailto:([^>]+)>', unsubscribe)
            if mailto_match:
                return f"mailto:{mailto_match.group(1)}"

        # Priority 3: Check other unsubscribe patterns in body
        if body:
            patterns = [
                r'https?://[^\s<>"]+(?:unsubscribe|opt[_-]?out|remove)[^\s<>"]*',
                r'<a\s+[^>]*href=["\'](https?://[^\s<>"]+(?:unsubscribe|opt[_-]?out|remove)[^\s<>"]*)["\'][^>]*>',
                r'(?:unsubscribe|opt[_-]?out|remove)[^<>]*?<a\s+[^>]*href=["\'](https?://[^\s<>"]+)["\'][^>]*>'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, body, re.IGNORECASE)
                if matches:
                    return matches[0]
        
        return None
    except Exception as e:
        print(f"Error extracting unsubscribe link: {str(e)}")
        return None

def get_all_emails(service, days="30", batch_size=100, progress_callback=None, max_retries=3):
    """Get emails with pagination, batch processing and categorization"""
    print("\n=== Starting email retrieval ===")
    
    # Handle "today" as a special case - use exact date range
    if isinstance(days, str) and days.lower() == "today":
        today = datetime.utcnow().date()
        query = f"after:{today} before:{today + timedelta(days=1)}"
    else:
        # Convert days to integer if it's a string
        try:
            days_int = int(days)
        except (ValueError, TypeError):
            days_int = 30  # Default fallback
            
        since_date = (datetime.utcnow() - timedelta(days=days_int)).date()
        query = f"after:{since_date}"
    print(f"Search query: {query}")

    senders = {}
    page_token = None
    processed_count = 0

    # Get estimate of total messages
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=1
    ).execute()

    total_messages = results.get('resultSizeEstimate', 1000)
    print(f"Total messages to process: {total_messages}")

    while True:
        try:
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=batch_size,
                pageToken=page_token
            ).execute()

            messages = results.get('messages', [])
            if not messages:
                print("No more messages to process")
                break

            for msg in messages:
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'List-Unsubscribe']
                ).execute()

                headers = msg_data['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                unsubscribe = next((h['value'] for h in headers if h['name'].lower() == 'list-unsubscribe'), None)

                if sender not in senders:
                    senders[sender] = {
                        'count': 0,
                        'emails': [],
                        'unsubscribe': unsubscribe
                    }

                    # Try to get unsubscribe link from body if not found in headers
                # Only try to get unsubscribe link if not already found in headers
                if not unsubscribe and 'List-Unsubscribe' not in [h['name'] for h in headers]:
                    try:
                        unsubscribe = get_unsubscribe_link(service, msg['id'])
                        senders[sender]['unsubscribe'] = unsubscribe
                    except Exception as e:
                        print(f"Error getting unsubscribe link: {str(e)}")
                        senders[sender]['unsubscribe'] = None

                senders[sender]['count'] += 1

                # Build email data (with unsubscribe link included)
                email_data = {
                    'id': msg['id'],
                    'subject': subject,
                    'category': categorize_email(subject, sender),
                    'unsubscribe': senders[sender]['unsubscribe']  # <-- added here
                }

                if 'internalDate' in msg_data:
                    email_data['date'] = datetime.fromtimestamp(int(msg_data['internalDate']) / 1000).strftime('%Y-%m-%d')
                else:
                    email_data['date'] = 'Unknown date'

                senders[sender]['emails'].append(email_data)

                print(f"Processed email: Subject: {subject}, Sender: {sender}, Date: {email_data['date']}")
                processed_count += 1

                if progress_callback:
                    progress = min(100, int((processed_count / total_messages) * 100))
                    progress_callback(progress, processed_count, total_messages)

            page_token = results.get('nextPageToken')
            if not page_token:
                print("No more pages to process")
                break

        except Exception as e:
            print(f"Error processing batch: {e}")
            break

    return senders

def unsubscribe_email(service, msg_id, unsubscribe_link):
    """Unsubscribe from emails using the unsubscribe link"""
    if unsubscribe_link is None:
        print("No unsubscribe link available")
        # Try to find one if not provided
        unsubscribe_link = get_unsubscribe_link(service, msg_id)
        if not unsubscribe_link:
            print("Could not find any unsubscribe link")
            return False
        
    if "mailto:" in unsubscribe_link:
        # Extract email and subject for mailto links
        import re
        email_match = re.search(r'mailto:([^\?]+)(?:\?subject=([^&]+))?', unsubscribe_link)
        if email_match:
            email = email_match.group(1)
            subject = email_match.group(2) if email_match.lastindex > 1 else "Unsubscribe"
            
            # Create a draft email for unsubscribing
            try:
                from email.mime.text import MIMEText
                import base64
                
                message = MIMEText("Please unsubscribe me from this mailing list.")
                message['to'] = email
                message['subject'] = subject
                
                raw_message = base64.urlsafe_b64encode(message.as_string().encode()).decode()
                
                service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
                
                print(f"Unsubscribe email sent to {email}")
                return True
            except Exception as e:
                print(f"Error sending unsubscribe email: {str(e)}")
                return False
        else:
            print("Invalid mailto: format in unsubscribe link")
            return False
    elif "http" in unsubscribe_link:
        import webbrowser
        print(f"Opening unsubscribe link: {unsubscribe_link}")
        webbrowser.open(unsubscribe_link)
        return True
    else:
        print("No valid unsubscribe link provided")
        return False

def delete_emails_by_sender(service, sender_email):
    """Delete all emails from a specific sender"""
    query = f'from:{sender_email}'
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    for msg in messages:
        service.users().messages().delete(userId='me', id=msg['id']).execute()

def bulk_action_by_criteria(service, action, criteria, dry_run=True):
    """Perform bulk actions (delete, archive, label) based on complex criteria
    
    Args:
        service: Gmail API service
        action: 'delete', 'archive', 'label', etc.
        criteria: Dict with criteria like {'older_than_days': 90, 'category': 'Promotions', 
                  'sender_contains': ['newsletter'], 'unread': True}
        dry_run: If True, only simulate the action
    """
    query_parts = []
    
    if 'older_than_days' in criteria:
        date = (datetime.utcnow() - timedelta(days=criteria['older_than_days'])).strftime('%Y/%m/%d')
        query_parts.append(f"before:{date}")
    
    if 'category' in criteria:
        if criteria['category'] == 'Promotions':
            query_parts.append("category:promotions")
        elif criteria['category'] == 'Social':
            query_parts.append("category:social")
    
    if 'sender_contains' in criteria:
        sender_queries = [f"from:(*{term}*)" for term in criteria['sender_contains']]
        query_parts.append(f"({' OR '.join(sender_queries)})")
    
    if 'unread' in criteria and criteria['unread']:
        query_parts.append("is:unread")
    
    query = " ".join(query_parts)
    print(f"Query: {query}")
    
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    print(f"Found {len(messages)} messages matching criteria")
    
    if dry_run:
        print("Dry run - no actions performed")
        return len(messages)
    
    if action == 'delete':
        for msg in messages:
            service.users().messages().trash(userId='me', id=msg['id']).execute()
    elif action == 'archive':
        for msg in messages:
            service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['INBOX']}).execute()
    elif action == 'label':
        label_name = criteria.get('label', 'Custom_Label')
        # Create label if it doesn't exist
        try:
            label = service.users().labels().create(userId='me', body={'name': label_name}).execute()
        except:
            # Label might already exist
            labels = service.users().labels().list(userId='me').execute()
            label = next((l for l in labels.get('labels', []) if l['name'] == label_name), None)
        
        if label:
            for msg in messages:
                service.users().messages().modify(
                    userId='me', 
                    id=msg['id'], 
                    body={'addLabelIds': [label['id']]}
                ).execute()
    
    return len(messages)


def generate_email_analytics(senders):
    """Generate analytics and insights from email data"""
    analytics = {
        'total_emails': sum(sender_data['count'] for sender_data in senders.values()),
        'total_senders': len(senders),
        'category_distribution': {},
        'top_senders': [],
        'time_analysis': {},
        'unsubscribe_opportunities': []
    }

    all_emails = []

    # Build email list and category distribution
    for sender, data in senders.items():
        for email in data['emails']:
            all_emails.append(email)
            category = email.get('category', 'Uncategorized')
            analytics['category_distribution'][category] = analytics['category_distribution'].get(category, 0) + 1

    # Top 10 senders by email count
    sorted_senders = sorted(senders.items(), key=lambda x: x[1]['count'], reverse=True)
    analytics['top_senders'] = [
        {'sender': sender, 'count': data['count']}
        for sender, data in sorted_senders[:10]
    ]

    # Time-based analysis (monthly breakdown)
    for email in all_emails:
        date = email.get('date', 'Unknown date')
        if date != 'Unknown date':
            month = date[:7]  # Format: YYYY-MM
            analytics['time_analysis'][month] = analytics['time_analysis'].get(month, 0) + 1

    # Unsubscribe opportunities — senders with >5 emails and unsubscribe links
    for sender, data in sorted_senders:
        # if data['count'] > 5 and data.get('unsubscribe'):
        if data.get('unsubscribe'):
            analytics['unsubscribe_opportunities'].append({
                    'sender': sender,
                    'count': data['count'],
                    'unsubscribe': data['unsubscribe']
                })    

    return analytics

def create_email_rule(service, rule_name, conditions, actions):
    """Create automated rules for email management
    
    Args:
        service: Gmail API service
        rule_name: Name of the rule
        conditions: Dict with conditions like {'from': 'newsletter@example.com', 'subject_contains': ['weekly']}
        actions: Dict with actions like {'move_to': 'Newsletters', 'mark_read': True}
    """
    # Store rules in a JSON file
    rules_file = 'email_rules.json'
    rules = []
    
    if os.path.exists(rules_file):
        with open(rules_file, 'r') as f:
            rules = json.load(f)
    
    # Add new rule
    rules.append({
        'name': rule_name,
        'conditions': conditions,
        'actions': actions,
        'created_at': datetime.now().isoformat()
    })
    
    # Save rules
    with open(rules_file, 'w') as f:
        json.dump(rules, f, indent=2)
    
    print(f"Rule '{rule_name}' created successfully")
    return True

def apply_email_rules(service):
    """Apply all defined rules to incoming emails"""
    rules_file = 'email_rules.json'
    if not os.path.exists(rules_file):
        print("No rules defined")
        return
    
    with open(rules_file, 'r') as f:
        rules = json.load(f)
    
    # Get recent emails (last 24 hours)
    query = f"after:{(datetime.utcnow() - timedelta(days=1)).strftime('%Y/%m/%d')}"
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject']
        ).execute()
        
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        
        # Check each rule
        for rule in rules:
            conditions_met = True
            
            # Check conditions
            if 'from' in rule['conditions'] and rule['conditions']['from'] not in sender:
                conditions_met = False
            
            if 'subject_contains' in rule['conditions']:
                if not any(term in subject for term in rule['conditions']['subject_contains']):
                    conditions_met = False
            
            # Apply actions if conditions are met
            if conditions_met:
                print(f"Applying rule '{rule['name']}' to email: {subject}")
                
                if 'move_to' in rule['actions']:
                    label_name = rule['actions']['move_to']
                    # Get or create label
                    labels = service.users().labels().list(userId='me').execute()
                    label = next((l for l in labels.get('labels', []) if l['name'] == label_name), None)
                    
                    if not label:
                        label = service.users().labels().create(
                            userId='me', 
                            body={'name': label_name}
                        ).execute()
                    
                    # Apply label and remove from inbox
                    service.users().messages().modify(
                        userId='me',
                        id=msg['id'],
                        body={
                            'addLabelIds': [label['id']],
                            'removeLabelIds': ['INBOX']
                        }
                    ).execute()
                
                if rule['actions'].get('mark_read', False):
                    service.users().messages().modify(
                        userId='me',
                        id=msg['id'],
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                
                if rule['actions'].get('delete', False):
                    service.users().messages().trash(userId='me', id=msg['id']).execute()

def analyze_email_importance(service, msg_id):
    """Analyze email content and score its importance"""
    msg_data = service.users().messages().get(
        userId='me',
        id=msg_id,
        format='full'
    ).execute()
    
    headers = msg_data['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
    
    # Extract email body
    body = ""
    if 'parts' in msg_data['payload']:
        for part in msg_data['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
    elif 'body' in msg_data['payload'] and 'data' in msg_data['payload']['body']:
        body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')
    
    # Calculate importance score (0-100)
    score = 50  # Default medium importance
    
    # Factors that increase importance
    importance_keywords = ['urgent', 'important', 'action', 'required', 'deadline', 'asap']
    if any(keyword in subject.lower() for keyword in importance_keywords):
        score += 20
    
    # Check if email is addressed directly to user
    user_info = service.users().getProfile(userId='me').execute()
    user_email = user_info['emailAddress']
    if f"To: {user_email}" in str(headers):
        score += 10
    
    # Check for questions in the email
    if '?' in body:
        score += 5
    
    # Check for dates/times (potential meetings/deadlines)
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
        r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}'  # Month DD
    ]
    if any(re.search(pattern, body.lower()) for pattern in date_patterns):
        score += 10
    
    # Normalize score to 0-100 range
    score = max(0, min(100, score))
    
    return {
        'id': msg_id,
        'subject': subject,
        'sender': sender,
        'importance_score': score,
        'analysis': {
            'has_urgency_keywords': any(keyword in subject.lower() for keyword in importance_keywords),
            'directly_addressed': f"To: {user_email}" in str(headers),
            'contains_questions': '?' in body,
            'contains_dates': any(re.search(pattern, body.lower()) for pattern in date_patterns)
        }
    }

def schedule_cleanup_task(service, criteria, frequency='weekly'):
    """Schedule regular email cleanup tasks
    
    Args:
        service: Gmail API service
        criteria: Dict with cleanup criteria
        frequency: 'daily', 'weekly', or 'monthly'
    """
    cleanup_tasks = []
    tasks_file = 'cleanup_tasks.json'
    
    if os.path.exists(tasks_file):
        with open(tasks_file, 'r') as f:
            cleanup_tasks = json.load(f)
    
    # Add new task
    task_id = str(len(cleanup_tasks) + 1)
    cleanup_tasks.append({
        'id': task_id,
        'criteria': criteria,
        'frequency': frequency,
        'last_run': None,
        'created_at': datetime.now().isoformat()
    })
    
    # Save tasks
    with open(tasks_file, 'w') as f:
        json.dump(cleanup_tasks, f, indent=2)
    
    print(f"Cleanup task scheduled with frequency: {frequency}")
    return task_id

def run_scheduled_cleanups(service):
    """Run all scheduled cleanup tasks that are due"""
    tasks_file = 'cleanup_tasks.json'
    if not os.path.exists(tasks_file):
        print("No cleanup tasks defined")
        return
    
    with open(tasks_file, 'r') as f:
        cleanup_tasks = json.load(f)
    
    now = datetime.now()
    updated_tasks = []
    
    for task in cleanup_tasks:
        should_run = False
        last_run = datetime.fromisoformat(task['last_run']) if task['last_run'] else None
        
        if not last_run:
            should_run = True
        elif task['frequency'] == 'daily' and (now - last_run).days >= 1:
            should_run = True

def analyze_senders(service):
    """Get sender statistics and email summaries"""
    senders = get_all_emails(service)
    analysis = []
    for sender, data in senders.items():
        analysis.append(f"Sender: {sender}\n"
                       f"Emails: {data['count']}\n"
                       f"Unsubscribe: {'Available' if data['unsubscribe'] else 'Not available'}\n"
                       f"Latest subject: {data['emails'][0]['subject']}\n")
    return senders, "\n".join(analysis)

def unsubscribe_all_from_sender(service, sender):
    """Unsubscribe from all emails from a specific sender"""
    senders = get_all_emails(service)
    if sender in senders and senders[sender]['unsubscribe']:
        unsubscribe_email(service, None, senders[sender]['unsubscribe'])
        return f"Unsubscribed from {sender}"
    return f"No unsubscribe link found for {sender}"

def get_email_details(service, sender):
    """Get detailed email information for a sender"""
    senders = get_all_emails(service)
    if sender in senders:
        details = [f"Subject: {email['subject']}\nDate: {email['date']}\nID: {email['id']}\n"
                  for email in senders[sender]['emails']]
        return "\n".join(details)
    return f"No emails found from {sender}"

def bulk_unsubscribe(service, senders):
    """Unsubscribe from multiple senders at once"""
    results = []
    for sender in senders:
        result = unsubscribe_all_from_sender(service, sender)
        results.append(result)
    return "\n".join(results)