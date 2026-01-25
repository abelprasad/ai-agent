from dotenv import load_dotenv
load_dotenv()

from tools.email import EmailTool

# Test email tool directly  
email_tool = EmailTool()
result = email_tool.execute(
    subject="Test from AI Agent",
    body="This is a test email to verify Gmail SMTP is working."
)

print("Email result:", result)
