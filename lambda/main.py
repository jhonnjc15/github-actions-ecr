def lambda_handler(event, context):
    print("Prueba!")
    return {"ok": True, "event": event}