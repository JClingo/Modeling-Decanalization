"""Completion guards, durable receipt, and Windows notification dispatch."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

module_path=Path(__file__).resolve().parents[2]/'Content/Python/trial_notifications.py'
spec=importlib.util.spec_from_file_location('trial_notifications',module_path)
notifications=importlib.util.module_from_spec(spec);spec.loader.exec_module(notifications)

class CompletionTests(unittest.TestCase):
    def setUp(self):
        root=Path('Saved/TrialCompletionFix');root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root);self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name).resolve()/'run.yml';self.path.write_text('trials: []\n')
        self.props={'IsTrialMode':True,'TrialsRun':3,'TrialsToRun':3,'TrialFileName':str(self.path),'TrialYML':'trials: []\r\n'}
        gm=Mock();gm.get_editor_property.side_effect=self.props.__getitem__
        self.unreal=Mock();self.unreal.GameplayStatics.get_game_mode.return_value=gm
        self.unreal.Paths.convert_relative_path_to_full.side_effect=str
        self.unreal.Paths.engine_dir.return_value='D:/Dev/UE_5.5/Engine'
        self.unreal.SystemLibrary.get_command_line.return_value=''
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules,unreal=self.unreal).start()
        self.spawn=patch.object(notifications.subprocess,'Popen').start()

    def test_disabled_and_unfinished_do_not_notify(self):
        self.props['IsTrialMode']=False;notifications.notify_completed_trials()
        self.props['IsTrialMode']=True;self.props['TrialsRun']=2;notifications.notify_completed_trials()
        self.spawn.assert_not_called();self.assertFalse(self.path.with_suffix('.completed.json').exists())

    def test_saved_completion_spawns_hidden_dialog_once(self):
        notifications.notify_completed_trials();notifications.notify_completed_trials()
        receipt=json.loads(self.path.with_suffix('.completed.json').read_text())
        self.assertTrue(receipt['results_saved']);self.assertEqual(receipt['trials_completed'],3)
        self.spawn.assert_called_once()
        args,kwargs=self.spawn.call_args
        self.assertEqual(args[0][2],'--show-completion')
        self.assertEqual(kwargs['creationflags'],notifications.subprocess.CREATE_NO_WINDOW)
        self.assertIn(str(self.path),notifications.completion_message(receipt))

    def test_failed_save_is_reported(self):
        self.path.write_text('old contents')
        notifications.notify_completed_trials()
        receipt=json.loads(self.path.with_suffix('.completed.json').read_text())
        self.assertFalse(receipt['results_saved']);self.assertIn('WARNING',notifications.completion_message(receipt))

    def test_test_flag_suppresses_dialog_only(self):
        self.unreal.SystemLibrary.get_command_line.return_value='-NoTrialCompletionDialog'
        notifications.notify_completed_trials()
        self.spawn.assert_not_called();self.assertTrue(self.path.with_suffix('.completed.json').exists())
        self.assertIn('[TRIALS_COMPLETE]',self.unreal.log.call_args.args[0])

    def test_dialog_uses_expected_message(self):
        import ctypes
        api=Mock()
        with patch.object(ctypes,'windll',types.SimpleNamespace(user32=api)):
            notifications.show_dialog({'trials_completed':3,'trials_requested':3,'results_saved':True,'results_file':str(self.path)})
        api.MessageBoxW.assert_called_once()
        self.assertIn('All 3/3 trials',api.MessageBoxW.call_args.args[1])
        self.assertIn(str(self.path),api.MessageBoxW.call_args.args[1])

if __name__=='__main__':unittest.main()
