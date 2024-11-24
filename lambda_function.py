import asyncio
from main import main


def lambda_handler(event, context):
    try:
        # Run the async main function
        asyncio.get_event_loop().run_until_complete(main())

        return {"statusCode": 200, "body": "Successfully processed messages"}
    except Exception as e:
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
