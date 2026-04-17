FROM python AS pyzx-base

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -e .

FROM pyzx-base AS product

CMD ["python", "-c", "import pyzx_db_addon"]

FROM pyzx-base AS test-base
RUN pip install --no-cache-dir -e ".[test]"

FROM test-base AS tester

ENTRYPOINT [ "/bin/sh", "-c" ]

