"""AST condition checks for DRYRUN B1 signal suppression; no subprocess is run."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[2]


def method(file, class_name, name):
    tree=ast.parse((ROOT/file).read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name)
    return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)


def function(file,name):
    tree=ast.parse((ROOT/file).read_text())
    return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)


def evaluate(node,env):
    return eval(compile(ast.fix_missing_locations(ast.Expression(node)),'<condition>','eval'),env)


class DryrunStopSceneTests(unittest.TestCase):
    def test_server_start_preserves_b1_and_stagea_failures(self):
        node=method('r1/exam/runtime.py','ExamRunner','_server')
        call=next(n for n in ast.walk(node) if isinstance(n,ast.Call) and
                  isinstance(n.func,ast.Attribute) and n.func.attr=='start' and
                  any(k.arg=='preserve_on_failure' for k in n.keywords))
        value=next(k.value for k in call.keywords if k.arg=='preserve_on_failure')
        for phase,want in [('b1',True),('stage-a',True),('other',False)]:
            self.assertEqual(evaluate(value,{'self':SimpleNamespace(state={'phase':phase})}),want)

    def test_caught_dryrun_b1_failure_does_not_stop_worker(self):
        node=method('r1/exam/runtime.py','ExamRunner','run_job')
        branch=next(n for n in ast.walk(node) if isinstance(n,ast.If) and
                    any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and
                        x.func.id=='stop_tree' for stmt in n.body for x in ast.walk(stmt)))
        for phase,want in [('b1',False),('stage-a',False),('other',True)]:
            selfobj=SimpleNamespace(state={'phase':phase},child=SimpleNamespace(poll=lambda:None))
            self.assertEqual(evaluate(branch.test,{'self':selfobj}),want)

    def test_candidate_failure_does_not_stop_b1_server_but_normal_completion_does(self):
        node=function('r1/scripts/exam_runner.py','_evidence_unreviewed')
        branch=next(n for n in ast.walk(node) if isinstance(n,ast.If) and
                    any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and
                        x.func.attr=='stop_service' for stmt in n.body for x in ast.walk(stmt)) and
                    'candidate_failed' in ast.unparse(n.test))
        for phase,failed,want in [('b1',True,False),('b1',False,True),('other',True,True)]:
            env={'runner':SimpleNamespace(service=object()),'candidate_failed':failed,'phase':phase}
            self.assertEqual(bool(evaluate(branch.test,env)),want)

    def test_main_requests_preservation_for_failed_b1(self):
        node=function('r1/scripts/exam_runner.py','main')
        assignment=next(n for n in ast.walk(node) if isinstance(n,ast.Assign) and
                        any(isinstance(t,ast.Name) and t.id=='preserve_running' for t in n.targets) and
                        'a.phase' in ast.unparse(n.value))
        for phase,want in [('b1',True),('stage-a',True),('other',False)]:
            self.assertEqual(evaluate(assignment.value,{'a':SimpleNamespace(phase=phase)}),want)

    def test_loading_failure_does_not_stop_b1_server(self):
        node=method('r1/exam/runtime.py','ExamRunner','_server')
        branch=next(n for n in ast.walk(node) if isinstance(n,ast.If) and
                    any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and
                        x.func.attr=='stop' for stmt in n.body for x in ast.walk(stmt)) and
                    'inst.process' in ast.unparse(n.test))
        inst=SimpleNamespace(process=object(),record={'pgid':1})
        for phase,want in [('b1',False),('stage-a',False),('other',True)]:
            env={'self':SimpleNamespace(state={'phase':phase}),'inst':inst}
            self.assertEqual(bool(evaluate(branch.test,env)),want)

if __name__=='__main__': unittest.main()
