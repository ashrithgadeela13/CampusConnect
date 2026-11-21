"""Check the shipped pretrained encoder and the recommendations a student actually sees."""
import json
import os
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend import classifier, directory
from backend.db import connect
from backend.semantic import encoder


class SearchQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        old=os.environ.get("CAMPUSCONNECT_DATA_DIR")
        os.environ["CAMPUSCONNECT_DATA_DIR"]=cls.temp.name
        try:
            with closing(connect()) as db:
                cls.categories=directory.categories(db); cls.offices=directory.resources(db)
        finally:
            if old is None:os.environ.pop("CAMPUSCONNECT_DATA_DIR",None)
            else:os.environ["CAMPUSCONNECT_DATA_DIR"]=old

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def ask(self,question,rows=None):
        return classifier.classify(question,self.categories,self.offices if rows is None else rows)

    def test_model2vec_reference(self):
        # Reference values from the upstream Model2Vec StaticModel, using this exact checkpoint.
        m=encoder();self.assertIsNotNone(m)
        sentence="Where's my résumé?"
        self.assertEqual(m.tokens(sentence),[1079,11,61,1032,12752,35])
        v=m.encode(sentence);self.assertEqual(len(v),256)
        for a,b in zip(v,[.051804446,.173117787,-.047962755,.014669480,.043896552]):
            self.assertAlmostEqual(a,b,places=6)

    def test_service_contrasts_and_published_only(self):
        q="I want to drop a course and do it next semester"
        match=self.ask(q);self.assertEqual(match["method"],"model2vec")
        self.assertEqual(match["resourceIds"],["academic-advising","registrar"])
        self.assertEqual(match["matches"][0]["draft"],"advising-drop")
        self.assertEqual(match["matches"][1]["draft"],"registrar-drop")
        self.assertTrue(match["matches"][0]["source"]["url"].startswith("https://www.uta.edu/"))
        self.assertEqual(self.ask("Will dropping a class change my financial aid?")["resourceIds"][0],"financial-aid")
        self.assertEqual(self.ask("I need to drop off my borrowed textbook")["resourceIds"][0],"central-library")
        self.assertEqual(self.ask("My account")["state"],"clarify")
        self.assertEqual(self.ask("What is the capital of Finland?")["state"],"none")
        responses=self.ask(q,[{**r,"status":"archived"} if r["id"]=="registrar" else r for r in self.offices])
        self.assertNotIn("registrar",responses["resourceIds"])
        new={**self.offices[0],"id":"new","name":"Robotics Workshop","tags":"robotics,robot,actuator",
             "summary":"Build and repair robot actuators.","description":"A workshop for motor controllers and robot repairs."}
        self.assertEqual(self.ask("Robotics Workshop",[*self.offices,new])["resourceIds"][0],"new")
        self.assertNotIn("new",self.ask("Robotics Workshop",[*self.offices,{**new,"status":"archived"}])["resourceIds"])

    def test_office_level_evaluation(self):
        for dataset,minimum in (("office-checks.json",.90),("paraphrase-checks.json",.75)):
            cases=json.loads((ROOT/"ai"/dataset).read_text(encoding="utf-8"))
            answers=[self.ask(q)["resourceIds"][:1]==[office] for q,office in cases]
            print(f"{dataset}: expected first office on {sum(answers)}/{len(cases)} questions.",flush=True)
            self.assertGreaterEqual(sum(answers)/len(cases),minimum)

