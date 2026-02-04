import os
import unittest
# from dotenv import load_dotenv

# Load the specific file you created in the YAML
# load_dotenv(dotenv_path=".env.pyzx")

class TestConnectionWithNeo4j(unittest.TestCase):

    def test_has_envs(self):
        uri = os.getenv("NEO4J_URI")
        self.assertIsNotNone(uri)
        user = os.getenv("NEO4J_USER")
        self.assertIsNotNone(user)
        password = os.getenv("NEO4J_PASSWORD")
        self.assertIsNotNone(password)


if __name__ == "__main__":
    unittest.main()
