from langchain.agents import initialize_agent
from langchain_google_genai import GoogleGenerativeAI
from langchain.tools import Tool
from gmail_tools import (
    get_all_emails,
    unsubscribe_email,
    delete_emails_by_sender,

    bulk_action_by_criteria,
    generate_email_analytics,
    create_email_rule,
    apply_email_rules,
    analyze_email_importance,
    schedule_cleanup_task,
    advanced_categorization,
    bulk_unsubscribe,
    analyze_senders,
    categorize_email,
    get_unsubscribe_link,
    run_scheduled_cleanups,
    unsubscribe_all_from_sender,
    get_email_details
)
import os
from dotenv import load_env
load_env()

  # Replace with actual API key
llm = GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)


def make_agent(service):
    tools = [
       
        Tool(
            name="Get sender statistics",
            func=lambda _: analyze_senders(service)[1],
            description="Get statistics about email senders including count and unsubscribe availability"
        ),
        Tool(
            name="Unsubscribe from sender",
            func=lambda sender: unsubscribe_all_from_sender(service, sender),
            description="Unsubscribe from all emails from a specific sender"
        ),
        Tool(
            name="Delete all emails from sender",
            func=lambda sender: delete_emails_by_sender(service, sender),
            description="Permanently delete all emails from a specific sender"
        ),
        Tool(
            name="Get email details",
            func=lambda sender: get_email_details(service, sender),
            description="Get detailed information about emails from a specific sender"
        ),
        Tool(
            name="Unsubscribe from all bulk senders",
            func=lambda _: bulk_unsubscribe(service),
            description="Automatically unsubscribe from all senders with bulk/unwanted emails"
        ),
        Tool(
            name="Analyze email importance",
            func=lambda msg_id: analyze_email_importance(service, msg_id),
            description="Analyze and rank a specific email's importance. Requires message ID as input."
        ),
        Tool(
            name="Categorize emails",
            func=lambda _: categorize_email(service),
            description="Categorize emails into types like work, social, spam, etc."
        ),
        Tool(
            name="Advanced categorization",
            func=lambda _: advanced_categorization(service),
            description="Perform advanced categorization of your emails using AI"
        ),
        Tool(
            name="Generate email analytics",
            func=lambda _: generate_email_analytics(get_all_emails(service, days=30)),
            description="Generate analytics such as most active senders, categories, etc. Returns statistics about your email patterns."
        ),
        Tool(
            name="Create email rule",
            func=lambda rule: create_email_rule(service, rule),
            description="Create a custom email management rule, e.g., delete all from a sender or label them"
        ),
        Tool(
            name="Apply email rules",
            func=lambda _: apply_email_rules(service),
            description="Apply all the created email rules to your inbox"
        ),
        Tool(
            name="Schedule cleanup",
            func=lambda _: schedule_cleanup_task(service),
            description="Schedule regular cleanup tasks for your Gmail"
        ),
        Tool(
            name="Run scheduled cleanups",
            func=lambda _: run_scheduled_cleanups(service),
            description="Execute previously scheduled Gmail cleanup tasks"
        ),
        Tool(
            name="Perform bulk action by criteria",
            func=lambda criteria: bulk_action_by_criteria(service, criteria),
            description="Perform bulk actions (delete, label, etc.) based on specific criteria"
        ),
        Tool(
            name="Extract unsubscribe link from email",
            func=lambda msg_id: get_unsubscribe_link(service, msg_id),
            description="Extract an unsubscribe link from the headers or body of the email with the given message ID"
        ),
        Tool(
            name="Unsubscribe from email using link",
            func=lambda args: unsubscribe_email(service, args["msg_id"], args.get("unsubscribe_link")),
            description=(
                "Unsubscribe from an email using the unsubscribe link. "
                "Provide a dictionary with 'msg_id' and optionally 'unsubscribe_link'. "
                "If 'unsubscribe_link' is not provided, it will try to extract one automatically."
            )
        ), 
         Tool(
            name="List recent emails",
            func=lambda days=10: str(get_all_emails(service, days=days)),
            description="List all emails received in the last N days. Returns dictionary of senders with email data. Provide number of days like 7 or 10."
        ),
    ]

    return initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)