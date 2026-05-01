# Offizielles AWS Lambda Python 3.11 Base-Image
# Enthält bereits den Lambda Runtime Interface Client
FROM public.ecr.aws/lambda/python:3.11

# Abhängigkeiten installieren (zuerst, damit Docker-Layer gecacht werden)
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Anwendungscode kopieren
COPY app/ ${LAMBDA_TASK_ROOT}/app/

# Standard-Handler: FastAPI via Mangum
# Kann beim Erstellen des Lambda-Funktions überschrieben werden
# (z.B. für den Reminder-Lambda: cmd=["app.reminder.handler"])
CMD ["app.main.handler"]
