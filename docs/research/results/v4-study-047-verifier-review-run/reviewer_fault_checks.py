"""独立审查故障反例：仅控制面/只读合成生产字节，0抽签、0物理。"""
import json,os,signal,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
from scripts import verify_v4_middle_withdrawal as v
from scripts import middle_withdrawal_inputs as inputs
root=Path(__file__).parent/'reviewer-fault-epochs'
root.mkdir(exist_ok=False)
class IndependentFaultChecks(unittest.TestCase):
    def test_first_systemexit_survives_child_io_and_later_closing_faults(self):
        e=v.Epoch(root/'first-error',seconds=1,enforce_deadline=True);write=e.write;first=SystemExit(57);called=[]
        def work():
            e.active_case={'phase':'synthetic_partial','row':33};e.write('records.json',[]);raise first
        def close():called.append('closed');raise KeyboardInterrupt('later closer')
        def failing_write(name,value):
            if name=='proof.json':raise OSError('child proof failure')
            return write(name,value)
        with patch.object(e,'write',side_effect=failing_write),self.assertRaises(SystemExit) as caught:e.execute(work,(close,))
        self.assertIs(caught.exception,first);self.assertEqual(called,['closed'])
        meta=inputs.read(e.root/'metadata.json')
        self.assertEqual(meta['status'],'failed');self.assertEqual(meta['error'],'SystemExit(57)')
        self.assertEqual(meta['child_failure']['type'],'builtins.OSError');self.assertEqual(meta['child_failure']['message'],'child proof failure')
        self.assertIn('proof.json',meta['child_failure']['traceback']);self.assertEqual(inputs.read(e.root/'partial-case.json')['row'],33)
    def test_parent_systemexit_wait_kills_writer_before_failure_writer(self):
        g=v.Guard(time.monotonic(),1);real=os.waitpid;first=SystemExit('stop parent');calls=0
        def interrupted(pid,flags):
            nonlocal calls
            calls+=1
            if calls==1:raise first
            return real(pid,flags)
        def late():time.sleep(.08);(root/'late-success').write_text('bad')
        with patch.object(os,'waitpid',side_effect=interrupted),self.assertRaises(SystemExit) as caught:g.commit(late)
        self.assertIs(caught.exception,first);self.assertIsNone(getattr(g,'unreaped_child',None))
        g.commit(lambda:(root/'parent-failure-marker').write_text('failed'));time.sleep(.1)
        self.assertFalse((root/'late-success').exists());self.assertEqual((root/'parent-failure-marker').read_text(),'failed')
    def test_unconfirmed_writer_blocks_a_second_writer(self):
        g=v.Guard(time.monotonic(),1);g.unreaped_child=999999
        with patch.object(os,'fork') as fork,self.assertRaisesRegex(RuntimeError,'not confirmed'):g.commit(lambda:None)
        fork.assert_not_called()
    def test_producer_byte_change_captured_even_when_json_object_same(self):
        directory=root/'producer';directory.mkdir();source=directory/'records.json';source.write_text('[]\n')
        e=v.Epoch(root/'producer-drift',seconds=1,enforce_deadline=True)
        def work():e.capture([str(source)]);source.write_text('[ ]\n');e.write('records.json',[])
        with self.assertRaisesRegex(ValueError,'unchanged complete inputs'):e.execute(work)
        m=inputs.read(e.root/'metadata.json');self.assertEqual(m['status'],'failed')
        self.assertNotEqual(m['input_sha256'][str(source)],m['input_sha256_after'][str(source)])
    def test_expired_absolute_start_cannot_run_work(self):
        e=v.Epoch(root/'expired-before-work',seconds=1,enforce_deadline=True,started=time.monotonic()-2)
        with patch.object(v,'draw_future') as draw,self.assertRaises(inputs.DeadlineExpired):e.execute(draw)
        draw.assert_not_called();self.assertEqual(e.meta['status'],'failed')
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.,0.))
    def test_alarm_arm_error_runs_no_work_and_restores_handler(self):
        g=v.Guard(time.monotonic(),1);before=signal.getsignal(signal.SIGALRM);real=signal.setitimer;first=OSError('arm lease failed')
        def fail(which,seconds,*args):
            if seconds:raise first
            return real(which,seconds,*args)
        g.install()
        try:
            with patch.object(signal,'setitimer',side_effect=fail),patch.object(v,'draw_future') as draw,self.assertRaises(OSError) as caught:g.call(draw)
            self.assertIs(caught.exception,first);draw.assert_not_called();self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.,0.))
        finally:g.release()
        self.assertEqual(signal.getsignal(signal.SIGALRM),before)
if __name__=='__main__':
    with patch.object(v,'physical_step',side_effect=AssertionError('physics forbidden')) as physics,patch.object(v,'draw_future',side_effect=AssertionError('future forbidden')) as future:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentFaultChecks))
        physics.assert_not_called();future.assert_not_called()
    print(json.dumps({'physical_steps':0,'future_ticks':0,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}))
    sys.exit(not result.wasSuccessful())
