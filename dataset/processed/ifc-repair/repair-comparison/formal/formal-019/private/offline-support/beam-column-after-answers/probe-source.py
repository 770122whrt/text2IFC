"""019 complete bound execution after prewritten answers; no Provider calls.

The initial request and every old probe remain unchanged. Standard property
authorization uses the existing exact IFC2X3 registry resolver. Evidence is
inside the candidate package so it remains inspectable after archival.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import traceback

HERE = Path(__file__).absolute().parent
REPO = next(parent for parent in HERE.parents if (parent / "pyproject.toml").is_file() and (parent / "src/text2ifc_ifc_repair").is_dir())
BASE = REPO / ".tmp/repair-comparison-formal-expansion"
PACKAGE = next((parent for parent in [HERE,*HERE.parents] if parent.name=="formal-019" and (parent / "private/task.json").is_file()),
               BASE / "next-ten-packages/formal-019")
ROOT = PACKAGE / "private/offline-support/beam-column-after-answers"
sys.path[:0] = [str(HERE),str(REPO),str(REPO / "src"),str(BASE)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=str)+"\n",encoding="utf-8")


def direct_value(entity, set_name: str, property_name: str) -> list[dict]:
    rows=[]
    for relation in entity.IsDefinedBy:
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        pset=relation.RelatingPropertyDefinition
        if not pset.is_a("IfcPropertySet") or pset.Name!=set_name:
            continue
        for prop in pset.HasProperties:
            if prop.is_a("IfcPropertySingleValue") and prop.Name==property_name:
                value=prop.NominalValue
                rows.append({"value":value.wrappedValue if value is not None else None,
                             "value_type":value.is_a() if value is not None else None,
                             "unit":str(prop.Unit) if prop.Unit is not None else None,
                             "scope":"occurrence_direct"})
    return rows


def run() -> dict:
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    import numpy as np
    from next_ten_mesh_audit import mesh_agreement
    from scripts.ifc_repair.offline.run_phase12_public_structural_repair import _run_public_repair_with_resolver
    from text2ifc_ifc_repair.apply import apply_changeset
    from text2ifc_ifc_repair.operations import create_default_registry
    from text2ifc_ifc_repair.operations.column import column_operation_definition
    from text2ifc_ifc_repair.registry import OperationRegistry
    from text2ifc_knowledge.property_search import create_historical_alias_baseline_resolver

    started=time.monotonic()
    if ROOT.exists():
        raise FileExistsError("AFTER_ANSWER_EVIDENCE_ALREADY_EXISTS")
    task=read(PACKAGE / "private/task.json")
    numeric=read(PACKAGE / "private/geometry-review.json")["targets"]
    card=read(PACKAGE / "private/answer-card.json")
    if task["review"]["status"]!="pending_human_review" or task["budget"]["provider_calls_allowed"]:
        raise ValueError("DRAFT_OFFLINE_SCOPE_CHANGED")
    if card["required_user_facts"]!=["beam_load_bearing","column_load_bearing"] or any(card["facts"][key]["value"] is not True for key in card["required_user_facts"]):
        raise ValueError("PREWRITTEN_BOOLEAN_ANSWERS_CHANGED")
    ROOT.mkdir(parents=True)
    shutil.copy2(Path(__file__),ROOT / "probe-source.py")
    shutil.copy2(BASE / "next_ten_mesh_audit.py",ROOT / "next_ten_mesh_audit.py")
    protected=[REPO / task["source"]["source_path"],PACKAGE / "public/model.ifc",PACKAGE / "public/request.txt",PACKAGE / "private/reference.ifc",
               PACKAGE / "private/mutation/damaged.ifc",BASE / "next_ten_offline_structural_probe.json"]
    before={str(path.relative_to(REPO)):sha(path) for path in protected}
    initial=(PACKAGE / "public/request.txt").read_text(encoding="utf-8").strip()
    answers=[{"fact_id":key,"answer_text":card["facts"][key]["answer_text"],"value":True,
              "provenance":"prewritten candidate answer card; deterministic offline fixture, not a real user/model turn"}
             for key in card["required_user_facts"]]
    request=initial+"\n\n澄清答复（离线预写事实）：\n"+"\n".join(answer["answer_text"] for answer in answers)
    (ROOT / "request-initial.txt").write_text(initial+"\n",encoding="utf-8")
    (ROOT / "request-after-answers.txt").write_text(request+"\n",encoding="utf-8")
    write(ROOT / "simulated-clarification.json",{"questions_generated":False,"model_calls":0,"human_reply_observed":False,
                                                "facts_preprovided_for_execution_only":True,"answers":answers})
    damaged=ROOT / "model.ifc"
    shutil.copy2(PACKAGE / "public/model.ifc",damaged)
    operations=[]
    for index,row in enumerate(numeric,1):
        family=row["family"]
        answer=next(answer for answer in answers if answer["fact_id"]==f"{family}_load_bearing")
        operations.append({"operation_id":f"{family}-{index}","operation_type":f"add_{family}",
                           "target_query":{"schema_version":"text2ifc/ifc-target-query/0.1",
                                           "allowed_ifc_classes":["IfcBuildingStorey"],
                                           "geometry_constraints":[{"field":"storey_elevation_mm","value":row["storey_attribute_elevation_m"]*1000.0,"tolerance_mm":0.1}]},
                           "parameters":deepcopy(row["parameters_storey_local_mm"]),
                           "property_intents":[{"intent_kind":"exact_property","set_name":f"Pset_{family.title()}Common",
                                                "property_name":"LoadBearing","raw_value":True,"raw_unit":None,
                                                "requested_value_type":"IfcBoolean","scope":"occurrence_direct",
                                                "source":{"source_kind":"user_request","reference":f"request:/clarification/{answer['fact_id']}","excerpt":answer["answer_text"]}}]})
    bundle={"schema_version":"text2ifc/phase12-public-structural-request/0.1","case_id":"candidate-019-after-preset-answers",
            "request":request,"operations":operations}
    write(ROOT / "public-request.json",bundle)
    result=_run_public_repair_with_resolver(damaged_ifc=damaged,public_request_bundle=ROOT / "public-request.json",
                                             output_root=ROOT / "repair",property_knowledge_resolver=create_historical_alias_baseline_resolver())
    application=read(ROOT / "repair/application.json")
    changeset=read(ROOT / "repair/changeset.json")
    repaired=ifcopenshell.open(ROOT / "repair/repaired.ifc")
    # G is opened only after terminal publication, for independent measurement.
    gold=ifcopenshell.open(PACKAGE / "private/reference.ifc")
    unit_mm=ifcopenshell.util.unit.calculate_unit_scale(gold)*1000.0
    checks=[]
    for row,expectation,operation in zip(numeric,task["targets"],application["operations"],strict=True):
        family=row["family"]
        created=[item for item in operation["changes"]["created"] if item["ifc_class"]==f"Ifc{family.title()}"]
        if len(created)!=1:
            raise ValueError("EXPECTED_ONE_CREATED_OCCURRENCE_PER_OPERATION")
        entity=repaired.by_guid(created[0]["global_id"])
        storey=gold.by_guid(expectation["storey_global_id_private"])
        matrix=ifcopenshell.util.placement.get_local_placement(storey.ObjectPlacement).tolist()
        authored={"family":family,"frame":row["requested_geometry_support_frame"],"storey_world_matrix_project_units":matrix}
        shape_check=mesh_agreement(entity,authored,unit_mm)
        settings=ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS,True)
        mesh=ifcopenshell.geom.create_shape(settings,entity)
        vertices=np.asarray(mesh.geometry.verts,dtype=float).reshape(-1,3)
        bounds=np.array([[vertices[:,i].min(),vertices[:,i].max()] for i in range(3)])
        gold_bounds=np.asarray(expectation["bounds_world_m"],dtype=float)
        gold_bound_error=float(np.max(np.abs(bounds-gold_bounds))*1000.0)
        values=direct_value(entity,f"Pset_{family.title()}Common","LoadBearing")
        exact_property=len(values)==1 and values[0]["value"] is True and values[0]["value_type"]=="IfcBoolean" and values[0]["unit"] is None
        containing=list(entity.ContainedInStructure)
        checks.append({"family":family,"output_id":entity.GlobalId,"source_name_private":row["target_name"],
                       "shape_matches_authorized_public_geometry":shape_check["rectangular_mesh_matches_authored_axis_section"],
                       "shape_check":shape_check,"gold_world_bounds_max_error_mm":gold_bound_error,
                       "gold_deviation_within_prewritten_request_rounding":gold_bound_error<=1.0,
                       "preparation_rounding_bound_mm_not_formal_scoring_tolerance":1.0,
                       "LoadBearing":values,"exact_direct_IfcBoolean_true":exact_property,
                       "unique_correct_containment":len(containing)==1 and containing[0].RelatingStructure.GlobalId==expectation["storey_global_id_private"]})
    semantic_assignments=[]
    for operation in changeset["operations"]:
        assignments=[assignment for assignment in operation["semantic_assignments"] if assignment["fact_key"].endswith(".LoadBearing")]
        family=operation["operation_type"].removeprefix("add_")
        passed=len(assignments)==1 and assignments[0]["value"] is True and assignments[0]["value_type"]=="IfcBoolean" and assignments[0]["scope"]==f"{family}_occurrence"
        semantic_assignments.append({"operation_id":operation["operation_id"],"passed":passed,"assignments":assignments})

    # An explicitly labelled injected second-operation failure checks that the
    # happy-path whole-task transaction never publishes a partial first repair.
    registry=create_default_registry()
    # Use a fresh registry rather than duplicate-registering the Column.
    atomic_registry=OperationRegistry()
    for operation_type in registry.operation_types:
        definition=registry.require(operation_type)
        if definition.operation_type=="add_column":
            definition=replace(column_operation_definition(),postcondition_checker=lambda **kwargs:{
                "valid":False,"checks":[],"issues":[{"code":"INJECTED_OFFLINE_SECOND_OPERATION_FAILURE","path":"/postconditions","message":"Explicit offline atomic rollback probe"}]})
        atomic_registry.register(definition)
    negative_output=ROOT / "atomic-must-not-publish.ifc"
    negative=apply_changeset(damaged_ifc_path=damaged,repair_request=request,changeset=changeset,output_path=negative_output,registry=atomic_registry)
    write(ROOT / "injected-atomic-rollback.json",negative)
    rollback_passed=negative.get("valid") is False and negative.get("published") is False and not negative_output.exists() and any(issue.get("code")=="INJECTED_OFFLINE_SECOND_OPERATION_FAILURE" for issue in negative.get("issues",[])) and sha(damaged)==task["damaged_sha256"]
    unchanged=all(sha(path)==before[str(path.relative_to(REPO))] for path in protected)
    comparison=read(ROOT / "repair/comparison.json")
    outcome={"schema_version":"repair-comparison-bound-after-answers-support/0.1","case":"019",
             "timestamp":datetime.now(timezone.utc).isoformat(),"status":result["status"],"operation_count":result["operation_count"],
             "one_atomic_changeset":result["one_atomic_changeset"],"atomic_second_operation_rollback_passed":rollback_passed,
             "checks":checks,"semantic_assignments":semantic_assignments,
             "complete_preservation_success":comparison["complete_preservation_success"],"protected_source_D_request_and_old_probe_unchanged":unchanged,
             "evidence_class":"offline_bound_after_prewritten_answers_geometry_and_exact_property_execution_only",
             "standard_property_resolution":"existing checked-in exact IFC2X3 registry; no retrieval model, reranker or network",
             "questions_generated":False,"initial_natural_clarification_or_resume_tested":False,"full_B_experiment_runtime_verified":False,
             "provider_calls":0,"private_gold_supplied_to_repair":False,"human_review_status":"pending_human_review",
             "relative_evidence_directory":"private/offline-support/beam-column-after-answers","seconds":time.monotonic()-started}
    outcome["passed"]=result["status"]=="passed" and result["operation_count"]==2 and result["one_atomic_changeset"] and rollback_passed and unchanged and comparison["complete_preservation_success"] and all(all(row[key] for key in ("shape_matches_authorized_public_geometry","gold_deviation_within_prewritten_request_rounding","exact_direct_IfcBoolean_true","unique_correct_containment")) for row in checks) and all(row["passed"] for row in semantic_assignments)
    write(ROOT / "result.json",outcome)
    (ROOT / "README.md").write_text("# formal-019 答复明确后的离线支持检查\n\n初始请求未变；两项预写Boolean答案作为确定性离线夹具提供。未生成模型问题或观察真实人答，未调用模型。\n\n"
        "此目录自包含D、初始请求、模拟答复、答后绑定输入、完整resolve/bind/semantic manifest/atomic apply/reopen/evaluation/preservation输出和人工注入的第二操作回滚记录。\n\n"
        "主结果：result.json；正常产物：repair/repaired.ifc；回滚证据：injected-atomic-rollback.json。以相对路径阅读，不依赖外部.tmp目录。\n\n"
        "标准属性仅使用现有IFC2X3 exact registry解析，不证明自然语言检索或完整B运行时。独立原件几何比较发生在正式产物发布后，private/reference.ifc仅供评估。\n",encoding="utf-8")
    return outcome


if __name__=="__main__":
    try:
        outcome=run()
        print(json.dumps({key:outcome[key] for key in ("case","status","passed","operation_count","atomic_second_operation_rollback_passed","seconds")},ensure_ascii=True),flush=True)
        raise SystemExit(0 if outcome["passed"] else 1)
    except Exception:
        traceback.print_exc()
        raise
