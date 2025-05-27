from twilio.rest import Client
account_sid = 'ACd67d920e2f8354696051a98d2d444815'
auth_token = '72bad703cab77f165d3841184f5890f9'
client = Client(account_sid, auth_token)
message = client.messages.create(from_='+18333450761',
    body='dfsa',
    to='+18777804236'
)
print(message.sid)