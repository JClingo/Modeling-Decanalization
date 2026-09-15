"""Collect the reviewed settings with exact native-export source locations."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
PROJECT = Path(r"C:\Users\jingo\Documents\Unreal Projects\decanalization")
ENGINE = Path(r"C:\Program Files\Epic Games\UE_5.5\Engine")
LABELS = ("study_candidate_5e508dd", "committed_b2ec222", "current")

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def property_row(label, asset, key):
    path = ROOT / "raw" / label / (asset + "_defaults.t3d")
    for line, text in enumerate(path.read_text().splitlines(), 1):
        if text.startswith("   " + key + "="):
            return {"value": text.strip().split("=", 1)[1], "source": path.relative_to(ROOT).as_posix(), "line": line}
    raise KeyError((label, asset, key))

def pin_row(label, asset, graph, node, pin):
    nodes = read_json(ROOT / "derived" / label / (asset + ".json"))
    selected = next(n for n in nodes if n["graph"] == graph and n["name"] == node)
    selected_pin = next(p for p in selected["pins"] if p["PinName"] == pin)
    return {"source": f"raw/{label}/{asset}.t3d", "graph": graph, "node": node, **selected_pin}

properties = {
    "BP_AgentManager": ["Policy Settings", "Critic Settings", "Trainer Settings", "Trainer Training Settings", "Training Game Settings", "Run Inference", "PolicySnapshot", "EncoderSnapshot", "Decoder Snapshot"],
    "BP_AgentTrainingEnv": ["Max Time", "Max Setpoint Distance"],
    "BP_GameMode": ["IsHRL", "IsTrialMode", "TrialSequenceOrder", "PeriodTickLength", "BasePassiveLossRate", "TrialsToRun", "PositiveAlphaHRL", "NegativeBetaHRL", "AlphaNF", "RandomStream", "SpawnerGridWidth", "SpawnerGridSpacing"],
    "BP_Agent": ["HorizonLength", "BaseMaxSpeed", "AgentHeight", "LookCost", "SetpointDistance", "CapsuleTraceRadius"],
    "BP_ResourceSpawner": ["SpawnRate"],
    "BP_Resource": ["RespawnRate", "BaseHomeostaticImpact", "MaxHomeostaticImpact", "DecanalizationFactor"],
    "BP_Tile": ["BaseHomeostaticImpact", "DecanalizationRateFactor", "OverlapCount", "ImpactLossFactor"],
}
data = {"scope": "Recovered implementation is authoritative for manuscript discrepancies by author instruction. The reporting basis uses the May 25 study-era environment archive and recovered HRL-1000/NF-4000 model identities. Final NF/HRL settings were shared except for the respective encoder/policy/decoder snapshots. Author-confirmed model selection and one evaluated policy per reward family are documented; exact cumulative environment-transition totals were not recovered.",
        "author_confirmation": {
            "source": "User clarification in this conversation following the initial extraction report",
            "statement": "The final NF and HRL trials used the same settings in BP_AgentManager and the other Blueprints; only the encoder, policy, and decoder snapshots generated during their respective training runs were changed.",
            "same_manager_and_environment_settings_between_nf_and_hrl": True,
            "changed_snapshot_components": ["encoder", "policy", "decoder"],
            "nf_trials_loaded_nf_snapshots": True,
            "hrl_trials_loaded_hrl_snapshots": True,
            "exact_filenames_explicitly_supplied": False,
            "shared_environment_values_explicitly_supplied": False,
            "recovered_implementation_authorized_as_source_of_truth": True,
        },
        "reporting_basis": {
            "environment_label": "study_candidate_5e508dd",
            "environment_commit": "5e508dd8b782",
            "environment_selection_reason": "Nearest retained commit before the final May 26 evaluation logs; assistant reporting choice stated explicitly in the manuscript under the author's instruction to use recovered implementation",
            "grid_width_parameter": 25,
            "base_passive_loss_parameter": 0.05,
            "model_identifiers": {"HRL": {"run": "2025-05-25_19-45-04", "snapshot_label": 1000}, "NF": {"run": "2025-05-25_20-27-19", "snapshot_label": 4000}},
            "historical_runtime_manifest_recovered": False,
            "evaluation_duration_unit": "ticks",
            "phase_ticks": 6000,
            "inference_seconds_conversion_claimed": False,
        },
        "author_model_selection": {
            "source": "User clarification in this conversation, with a representative TensorBoard screenshot",
            "search_method": "Trial and error across parameter variations",
            "attempted_parameter_variations_lower_bound_per_reward_family": 50,
            "varied_parameters": ["reward magnitudes", "punishment magnitudes", "resource reward size", "movement cost", "other parameters"],
            "selection_metric": "Average training reward",
            "candidate_selection": "Best average-reward candidate selected separately within NF and HRL",
            "snapshot_selection": "Point at which the improvement slope in average reward approached zero",
            "plateau_assessment": "Qualitative; no fixed numerical slope threshold supplied",
            "plateau_selection_motivation": "Avoid overfitting",
            "overfitting_prevention_demonstrated_by_plateau": False,
            "evaluation_started_after_model_selection": True,
            "selected_policies_evaluated": {"NF": 1, "HRL": 1, "total": 2},
            "evaluation_trials_per_condition": 50,
            "evaluation_trials_are_independent_training_replicates": False,
            "screenshot": {"file": "representative_training_dashboard.png", "sha256": sha(ROOT / "representative_training_dashboard.png"), "role": "Representative dashboard supplied by author; not proof of exact final-run identities or environment-step totals"},
        },
        "training_exposure": {
            "meaning": "Cumulative training represented by a selected snapshot, distinguished from a configured cap, later updates in the same run, and the entire exploratory search",
            "exact_environment_transitions_to_selected_snapshots_recovered": False,
            "exact_total_exploratory_search_transitions_recovered": False,
            "reported_evidence": "Snapshot identifiers, qualitative plateau selection rule, and retained optimizer index ranges in training_event_summary.json",
            "manuscript_treatment": "Explicitly states unrecovered totals; no invented counts or unresolved fill-in field",
        },
        "evaluation_memory_behavior": {
            "registration": "LearningAgentsPolicy.OnAgentsAdded initializes recurrent state to zero",
            "training_reset": "Learning Agents reset notifications zero recurrent state",
            "custom_phase_trial_reset": "Preserves the already registered agent's recurrent memory within the running evaluation session; no policy reset notification in reviewed Blueprint paths",
            "application_or_policy_recreation_carryover_claimed": False,
            "implementation_source": "LearningAgentsPolicy.cpp OnAgentsAdded_Implementation and OnAgentsReset_Implementation; retained BP_GameMode/BP_Agent/BP_AgentManager reset graphs",
        },
        "defaults": {label: {asset: {key: property_row(label, asset, key) for key in keys} for asset, keys in properties.items()} for label in LABELS},
        "graph_evidence": {}, "models": {}, "run_configs": {}}

pins = {
    "inference_action_noise": ("BP_AgentManager", "EventGraph", "K2Node_CallFunction_14", "ActionNoiseScale"),
    "policy_seed": ("BP_AgentManager", "EventGraph", "K2Node_CallFunction_1", "Seed"),
    "critic_seed": ("BP_AgentManager", "EventGraph", "K2Node_CallFunction_2", "Seed"),
    "reset_agents_on_training_begin": ("BP_AgentManager", "EventGraph", "K2Node_CallFunction_11", "bResetAgentsOnBegin"),
    "environment_seed": ("BP_GameMode", "EventGraph", "K2Node_CallFunction_41", "NewSeed"),
    "initial_training_h": ("BP_GameMode", "ResetValues", "K2Node_CallArrayFunction_0", "NewItem"),
    "initial_inference_h_min": ("BP_GameMode", "ResetValues", "K2Node_CallFunction_7", "Min"),
    "initial_inference_h_max": ("BP_GameMode", "ResetValues", "K2Node_CallFunction_7", "Max"),
    "phase_boundary_1": ("BP_GameMode", "RunTrial", "K2Node_PromotableOperator_12", "B"),
    "phase_boundary_2": ("BP_GameMode", "RunTrial", "K2Node_PromotableOperator_13", "B"),
    "phase_boundary_3": ("BP_GameMode", "RunTrial", "K2Node_PromotableOperator_14", "B"),
    "logged_duration_constant": ("BP_GameMode", "RunTrial", "K2Node_VariableSet_15", "SequenceDuration"),
    "pellet_minimum": ("BP_Resource", "EventGraph", "K2Node_CallFunction_8", "Min"),
    "tile_divisor_offset": ("BP_Tile", "EventGraph", "K2Node_PromotableOperator_16", "B"),
    "traversal_count_reduction_divisor": ("BP_Tile", "EventGraph", "K2Node_PromotableOperator_5", "B"),
    "action_float_scale": ("BP_AgentInteractor", "SpecifyAgentAction", "K2Node_CallFunction_1", "FloatScale"),
    "initial_yaw_min": ("BP_Agent", "EventGraph", "K2Node_CallFunction_66", "Min"),
    "initial_yaw_max": ("BP_Agent", "EventGraph", "K2Node_CallFunction_66", "Max"),
}
for index in range(7):
    pins["ray_angle_" + str(index)] = ("BP_AgentInteractor", "GatherAgentObservation", "K2Node_MakeArray_1", f"[{index}]")
for name, location in pins.items():
    data["graph_evidence"][name] = pin_row(LABELS[0], *location)

data["steering_audit"] = {
    "author_observation": {
        "approximate_value": 4.3,
        "measurement_point": "BP_AgentInteractor GetFloatAction output / AddControllerYawInput input pin",
        "measurement_point_confirmed_by_author": True,
        "kind": "Steering command before controller scaling; not measured actor angular displacement",
        "runtime_trace_collected_by_exporter": False,
    },
    "author_runtime_scale_confirmation": {
        "input_yaw_scale": 2.5,
        "source": "User explicitly confirmed runtime scale 2.5 in this conversation",
        "confirmed_by_author": True,
        "captured_by_exporter": False,
        "raw_action_bound_confirmed": False,
    },
    "action_model": "Continuous Gaussian parameterized by mean and log standard deviation; zero-noise inference selects the mean",
    "float_scale_role": "Multiplication when converting the sampled action vector into an action object; not a clamp",
    "explicit_action_clamp_found": False,
    "configured_4_3_cap_found": False,
    "action_regularization": {"weight": 0.001, "continuous_penalty": "abs(mean) + abs(log_std)", "hard_bound": False},
    "saved_controller_configuration": {
        "game_mode_player_controller_class": "/Script/Engine.PlayerController",
        "enable_legacy_input_scales": True,
        "base_game_input_yaw_scale": 2.5,
        "blueprint_or_project_config_yaw_scale_override_found": False,
        "runtime_scale_captured_by_exporter": False,
        "agent_uses_controller_yaw": True,
    },
    "yaw_input_formula": "RotationInput.Yaw += a_t * InputYawScale when legacy scales are enabled and look input is not ignored",
    "frame_delta_multiplies_yaw_input": False,
    "expected_requested_yaw_degrees_for_reported_command": 10.75,
    "expected_yaw_assumptions": "Effective runtime scale 2.5; local PlayerController; look input enabled; one action contribution; standard rotation processing",
    "inference": "Observed action magnitudes can reflect the learned policy over visited states; no global network maximum was computed",
    "runtime_check": "Scale 2.5 is author-confirmed. Record frame/decision index, action, control/actor yaw at observation gathering and after rotation processing, and action calls per frame; normalize yaw differences and exclude reset frames",
    "tick_timing": {
        "yaw_node_sets_actor_rotation_immediately": False,
        "input_behavior": "Accumulate scaled input; apply in PlayerTick/UpdateRotation; clear in TickActor after processing",
        "multiple_inputs_before_processing": "Sum",
        "run_inference_call_order": ["GatherObservations", "EncodeObservations", "EvaluatePolicy", "DecodeAndSampleActions", "PerformActions"],
        "regular_training_call_order": ["GatherCompletions", "GatherRewards", "ProcessExperience", "RunInference"],
        "retained_manager_tick_group": "TG_PrePhysics",
        "retained_manager_tick_interval": 0,
        "retained_blueprint_dependency": "Agent actor tick waits for BP_AgentManager actor tick",
        "manager_before_controller_or_movement_established": False,
        "runtime_tick_order_captured": False,
        "action_latency_measured": False,
        "learning_impairment_established": False,
        "further_tick_order_trace": "Optional troubleshooting; not required to document the recovered implementation",
    },
    "blueprint_evidence": {label: {
        "action_scale": pin_row(label, "BP_AgentInteractor", "SpecifyAgentAction", "K2Node_CallFunction_1", "FloatScale"),
        "yaw_input": pin_row(label, "BP_AgentInteractor", "PerformAgentAction", "K2Node_CallFunction_8427", "Val"),
        "player_controller_class": property_row(label, "BP_GameMode", "PlayerControllerClass"),
        "use_controller_yaw": property_row(label, "BP_Agent", "bUseControllerRotationYaw"),
        "manager_tick": property_row(label, "BP_AgentManager", "PrimaryActorTick"),
        "agent_tick_prerequisite": pin_row(label, "BP_AgentManager", "EventGraph", "K2Node_CallFunction_8", "PrerequisiteActor"),
        "agent_tick_prerequisite_target": pin_row(label, "BP_AgentManager", "EventGraph", "K2Node_CallFunction_8", "self"),
    } for label in LABELS},
    "source_locations": [
        {"file": str(ENGINE / "Plugins/Experimental/LearningAgents/Source/LearningAgents/Private/LearningAgentsActions.cpp"), "lines": [1110, 1113, 1737, 1788, 2789, 2823], "role": "Float schema delegates to continuous schema; action getter copies sampled value"},
        {"file": str(ENGINE / "Plugins/Experimental/LearningAgents/Source/Learning/Private/LearningAction.cpp"), "lines": [1292, 1303, 1766, 1782], "role": "Continuous Gaussian sampling and action-object scaling"},
        {"file": str(ENGINE / "Plugins/Experimental/LearningAgents/Source/Learning/Private/LearningRandom.cpp"), "lines": [290, 325], "role": "Zero-noise mean selection; noise log-standard-deviation cap is not an action bound"},
        {"file": str(ENGINE / "Plugins/Experimental/LearningAgents/Content/Python/train_common.py"), "lines": [1353, 1363], "role": "Continuous-action soft regularization"},
        {"file": str(ENGINE / "Plugins/Experimental/LearningAgents/Content/Python/ppo.py"), "lines": [321], "role": "Regularization weight applied to PPO loss"},
        {"file": str(ENGINE / "Source/Runtime/Engine/Private/Pawn.cpp"), "lines": [850, 856, 1049, 1078], "role": "Local PlayerController forwarding and direct control-to-actor rotation"},
        {"file": str(ENGINE / "Source/Runtime/Engine/Private/PlayerController.cpp"), "lines": [1014, 1046, 2415, 2419, 5316, 5317, 5714, 5717], "role": "Accumulated rotation processing, tick-end input clearing, and yaw input scaling"},
        {"file": str(ENGINE / "Source/Runtime/Engine/Private/Controller.cpp"), "lines": [489, 513], "role": "Native controller-before-pawn movement dependency"},
        {"file": str(ENGINE / "Plugins/Experimental/LearningAgents/Source/LearningAgents/Private/LearningAgentsPolicy.cpp"), "lines": [729, 743], "role": "Observation/policy/action sequence on every successful RunInference call"},
        {"file": str(ENGINE / "Plugins/Experimental/LearningAgents/Source/LearningAgentsTraining/Private/LearningAgentsPPOTrainer.cpp"), "lines": [678, 717], "role": "PPO rewards/experience then next inference"},
        {"file": str(ENGINE / "Source/Runtime/Engine/Private/PlayerCameraManager.cpp"), "lines": [53, 54, 1023, 1076], "role": "Absolute yaw wrapping/range, not per-tick steering cap"},
        {"file": str(ENGINE / "Config/BaseGame.ini"), "lines": [173], "role": "Base InputYawScale=2.5"},
        {"file": str(PROJECT / "Config/DefaultInput.ini"), "lines": [100], "role": "Legacy input scales enabled"},
    ],
}
for row in data["steering_audit"]["blueprint_evidence"].values():
    assert row["action_scale"]["DefaultValue"] == "1.000000"
    assert row["yaw_input"]["links"][0][0] == "K2Node_CallFunction_4"
    assert row["use_controller_yaw"]["value"] == "True"

ck = read_json(ROOT / "checkpoint_inventory.json")
arch = read_json(ROOT / "checkpoint_architectures.json")
for label in LABELS:
    data["models"][label] = []
    for path in sorted((ROOT / "raw" / label).glob("*.bin")):
        digest = sha(path)
        topology = next(x for x in arch if Path(x["file"]) == path)
        data["models"][label].append({"export": path.relative_to(ROOT).as_posix(), "sha256": digest,
            "matching_checkpoints": [x["file"] for x in ck if x["sha256"] == digest],
            "input_size": topology["input_size"], "output_size": topology["output_size"],
            "trainable_parameters": topology["trainable_parameter_count"]})

dest = ROOT / "raw" / "trainer_configs"
dest.mkdir(exist_ok=True)
for name, timestamp in (("HRL", "2025-05-25_19-45-04"), ("NF", "2025-05-25_20-27-19")):
    source = PROJECT / "Intermediate/LearningAgents/Configs" / ("Training_train_ppo_SharedMemory_" + timestamp + ".json")
    shutil.copyfile(source, dest / source.name)
    original = read_json(source)
    data["run_configs"][name] = {"source": str(source), "sha256": sha(source), "timestamp": original["TimeStamp"],
        **{k: original[k] for k in ("PPOSettings", "ReplayBuffers", "Schemas", "Networks")}}

engine_files = [
    "Plugins/Experimental/LearningAgents/Content/Python/train_ppo.py",
    "Plugins/Experimental/LearningAgents/Content/Python/ppo.py",
    "Plugins/Experimental/LearningAgents/Content/Python/train_common.py",
    "Plugins/Experimental/LearningAgents/Source/LearningAgents/Private/LearningAgentsActions.cpp",
    "Plugins/Experimental/LearningAgents/Source/Learning/Private/LearningAction.cpp",
    "Plugins/Experimental/LearningAgents/Source/Learning/Private/LearningRandom.cpp",
    "Plugins/Experimental/LearningAgents/Source/LearningAgentsTraining/Private/LearningAgentsPPOTrainer.cpp",
    "Plugins/Experimental/LearningAgents/Source/LearningAgentsTraining/Private/LearningAgentsTrainingEnvironment.cpp",
    "Plugins/Experimental/LearningAgents/Source/LearningAgents/Private/LearningAgentsPolicy.cpp",
    "Plugins/Experimental/NNERuntimeBasicCpu/Content/Python/nne_runtime_basic_cpu.py",
    "Plugins/Experimental/NNERuntimeBasicCpu/Content/Python/nne_runtime_basic_cpu_pytorch.py",
    "Source/Runtime/Engine/Private/PlayerController.cpp",
    "Source/Runtime/Engine/Private/Controller.cpp",
    "Source/Runtime/Engine/Private/Pawn.cpp",
    "Source/Runtime/Engine/Private/PlayerCameraManager.cpp", "Config/BaseGame.ini",
]
data["engine_sources"] = [{"file": str(ENGINE / f), "sha256": sha(ENGINE / f)} for f in engine_files]
(ROOT / "settings.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
print("Wrote settings.json; every requested property and graph pin found.")
