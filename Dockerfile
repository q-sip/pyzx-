FROM python AS pyzx-base

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


FROM pyzx-base AS product
COPY . .
RUN pip install -e .
CMD ["python", "-m", "manual_ohtu.main_switch"]

FROM pyzx-base AS test-base
COPY test_requirements.txt ./
RUN pip install --no-cache-dir -r test_requirements.txt


FROM test-base AS tester
COPY . .
ENTRYPOINT [ "/bin/sh", "-c" ]

