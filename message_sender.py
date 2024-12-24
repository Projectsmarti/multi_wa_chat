import os
import pandas as pd
import requests
import logging
import time
from datetime import datetime
from dotenv import load_dotenv


class WhatsAppSender:
    def __init__(self):
        """Initialize WhatsApp sender with credentials from .env file"""
        load_dotenv()

        self.access_token = os.getenv('META_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('PHONE_NUMBER_ID')

        if not self.access_token or not self.phone_number_id:
            raise ValueError("Please set META_ACCESS_TOKEN and PHONE_NUMBER_ID in .env file")

        self.base_url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            filename=f'whatsapp_logs_{datetime.now().strftime("%Y%m%d_%H%M")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        # Add console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        logging.getLogger('').addHandler(console)

    def clean_phone_number(self, phone: str) -> str:
        """Clean phone number to standard format"""
        # Remove any spaces or special characters
        clean = ''.join(filter(str.isdigit, str(phone)))
        return clean

    def send_template_message(self, to_phone: str, template_name: str, params: dict = None) -> dict:
        """
        Send a template message to a single number

        Args:
            to_phone: Recipient phone number
            template_name: Name of the approved template
            params: Dictionary of parameters for template
        """
        # Clean phone number
        to_phone = self.clean_phone_number(to_phone)

        # Prepare message data
        message_data = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "en"
                }
            }
        }

        # Add parameters if provided
        if params:
            components = []
            if params:
                component = {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(value)}
                        for value in params.values()
                    ]
                }
                components.append(component)
            message_data["template"]["components"] = components

        try:
            # Send message
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=message_data
            )

            # Check for errors
            response.raise_for_status()

            result = response.json()
            logging.info(f"Message sent successfully to {to_phone}")
            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to send message to {to_phone}"
            if hasattr(e.response, 'json'):
                error_msg += f": {e.response.json()}"
            logging.error(error_msg)
            raise Exception(error_msg)

    def process_excel(self, excel_file: str, sheet_name: str = 'Sheet1'):
        """
        Process contacts from Excel file and send messages

        Args:
            excel_file: Path to Excel file
            sheet_name: Name of the sheet containing contacts
        """
        try:
            # Read Excel file
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            # Validate required columns
            required_columns = ['phone_number', 'template_name']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Excel must contain columns: {required_columns}")

            results = {
                'successful': 0,
                'failed': 0,
                'failures': []
            }

            # Process each row
            total_rows = len(df)
            for index, row in df.iterrows():
                try:
                    # Get parameters from additional columns
                    params = {
                        col: row[col]
                        for col in df.columns
                        if col not in required_columns and pd.notna(row[col])
                    }

                    # Send message
                    self.send_template_message(
                        to_phone=row['phone_number'],
                        template_name=row['template_name'],
                        params=params
                    )

                    results['successful'] += 1
                    logging.info(f"Progress: {index + 1}/{total_rows}")

                    # Add delay between messages
                    if index < total_rows - 1:
                        time.sleep(1)

                except Exception as e:
                    results['failed'] += 1
                    results['failures'].append({
                        'phone': row['phone_number'],
                        'error': str(e)
                    })
                    logging.error(f"Failed for {row['phone_number']}: {str(e)}")

            return results

        except Exception as e:
            logging.error(f"Excel processing error: {str(e)}")
            raise


def main():
    try:
        # Initialize sender
        sender = WhatsAppSender()

        # Process Excel file
        results = sender.process_excel('contacts.xlsx')

        # Print summary
        print("\nProcessing Summary:")
        print(f"Successfully sent: {results['successful']}")
        print(f"Failed: {results['failed']}")

        if results['failures']:
            print("\nFailed numbers:")
            for failure in results['failures']:
                print(f"- {failure['phone']}: {failure['error']}")

    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()