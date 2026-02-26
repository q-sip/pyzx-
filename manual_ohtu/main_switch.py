# This one is wild one,
# just comment out others and leave your script open and everything should works.

# pylint: disable=W0611

from dotenv import load_dotenv
import os


# use this command to run
if __name__ == "__main__":

    print("Hello there!")
    load_dotenv()
    db = os.getenv("BACKEND_NAME", "memgraph")

    # Here the imports and usages:

    if db == "neo4j":
        from . import neo4j_functionality_test
        print("Neon done")

        pass
    if db == "memgraph":
        #from . import memgraph_functionality_test
        # from . import full_test
        #from . import full_test2
        #from . import zxdb_functionality_test
        from . import demo
        print("mem done")


        pass
    if db == "age":
        from . import age_functionality_test

        print("Age done")
        pass

    print("\n All things done :)")
