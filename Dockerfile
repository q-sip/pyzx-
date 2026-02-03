FROM python AS pyzx-base

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt



# CMD [ "python", "./neo4j_functionality_test.py" ]


FROM pyzx-base AS product
COPY . .





FROM pyzx-base AS tester
COPY test_requirements.txt ./
RUN pip install --no-cache-dir -r test_requirements.txt
WORKDIR /app
COPY . .
ENTRYPOINT [ "python", "-m",  "unittest",  "discover", "-v", "-s",  "tests/test_graph_neo4j" ]
