"""Notify after the final saved trial, including unattended headless runs.

Imported by the GameMode completion graph. The dialog runs in a separate,
hidden Python process so Unreal can finish quitting without dismissing it.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


def completion_message(receipt):
    message = 'All {}/{} trials are complete.'.format(receipt['trials_completed'], receipt['trials_requested'])
    if receipt['results_saved']:
        return message + '\n\nResults saved to:\n' + receipt['results_file']
    return message + '\n\nWARNING: The final YAML could not be verified on disk.\nCheck the Unreal log and:\n' + receipt['results_file']


def show_dialog(receipt):
    if os.name != 'nt':
        print(completion_message(receipt))
        return
    import ctypes
    icon = 0x40 if receipt['results_saved'] else 0x30
    ctypes.windll.user32.MessageBoxW(None, completion_message(receipt), 'Unreal trials complete', icon | 0x10000 | 0x40000)


def notify_completed_trials():
    import unreal

    # PIE exposes its world through the editor subsystem; standalone -game uses
    # the loaded Landscape world. Both paths target this project's GameMode.
    worlds = []
    try:
        worlds.append(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world())
    except Exception:
        pass
    worlds.append(unreal.find_object(None, '/Game/Level/Landscape.Landscape'))
    gm = next((unreal.GameplayStatics.get_game_mode(w) for w in worlds if w and unreal.GameplayStatics.get_game_mode(w)), None)
    if not gm:
        unreal.log_error('Cannot find GameMode for trial completion notification')
        return
    completed = gm.get_editor_property('TrialsRun')
    requested = gm.get_editor_property('TrialsToRun')
    if not gm.get_editor_property('IsTrialMode') or requested <= 0 or completed < requested:
        return
    raw_path = gm.get_editor_property('TrialFileName')
    if not raw_path:
        unreal.log_error('Trial completion has no YAML output path')
        return
    results = Path(unreal.Paths.convert_relative_path_to_full(raw_path))
    receipt_path = results.with_suffix('.completed.json')
    # A run emits one completion dialog, even if its final callback is repeated.
    if receipt_path.exists():
        return
    expected = gm.get_editor_property('TrialYML').replace('\r\n', '\n')
    try:
        actual = results.read_text(encoding='utf-8-sig')
        if '\nschema-version: 2\n' in actual:
            from trial_metrics import metadata_suffix
            metrics = json.loads(results.with_suffix('.metrics.json').read_text(encoding='utf-8'))
            saved = actual == expected + metadata_suffix(results) and metrics.get('status') == 'complete'
        else:
            saved = actual == expected
    except (OSError, ValueError):
        saved = False
    receipt = {
        'status': 'completed',
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
        'trials_completed': completed,
        'trials_requested': requested,
        'results_file': str(results),
        'results_saved': saved,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    unreal.log('[TRIALS_COMPLETE] ' + completion_message(receipt).replace('\n', ' '))
    if '-NoTrialCompletionDialog' in unreal.SystemLibrary.get_command_line().split():
        return
    try:
        python = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.engine_dir())) / 'Binaries/ThirdParty/Python3/Win64/python.exe'
        subprocess.Popen([str(python), str(Path(__file__).resolve()), '--show-completion', str(receipt_path)],
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         close_fds=True)
    except OSError as error:
        unreal.log_error('Could not display trial completion dialog: ' + str(error))


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--show-completion':
        raise SystemExit('Expected --show-completion <receipt.json>')
    show_dialog(json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')))
