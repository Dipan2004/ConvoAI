## WhatsApp Integration

Webhook receives incoming WhatsApp messages.
Extract the sender phone number and use it as the session_id.
Forward the message payload to the /chat endpoint.
Read the assistant response from the /chat result.
Send that response back to the user using the WhatsApp API.
