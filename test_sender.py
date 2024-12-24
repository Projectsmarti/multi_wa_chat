import os
from dotenv import load_dotenv
from message_sender import FacebookMessageSender


def test_single_message():
    """Test sending a single message"""
    sender = FacebookMessageSender(
        access_token=os.getenv('META_ACCESS_TOKEN'),
        page_id=os.getenv('META_PAGE_ID')
    )

    # Test with a single number
    test_number = "919042014905"  # Replace with your test number
    response = sender.send_template_message(
        phone_number=test_number,
        template_name="welcome_message",
        components=[
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "Test User"},
                    {"type": "text", "text": "CUST001"}
                ]
            }
        ]
    )
    print(f"Single message test response: {response}")


def test_bulk_messages():
    """Test sending bulk messages"""
    sender = FacebookMessageSender(
        access_token=os.getenv('META_ACCESS_TOKEN'),
        page_id=os.getenv('META_PAGE_ID')
    )

    # Test with excel file
    results = sender.process_bulk_messages('contacts.xlsx')
    print(f"Bulk message test results: {results}")


if __name__ == "__main__":
    load_dotenv()

    print("Starting single message test...")
    test_single_message()

    print("\nStarting bulk message test...")
    test_bulk_messages()