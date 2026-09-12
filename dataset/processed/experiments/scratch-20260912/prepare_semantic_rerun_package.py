from pathlib import Path
import shutil

base = Path('dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910')
parent = base/'appearance-guard-rerun-20260910'
out = base/'semantic-authority-rerun-20260910'
out.mkdir(exist_ok=False)
(out/'.gitattributes').write_text('* -text\n', encoding='utf-8')
shutil.copytree(parent/'inputs', out/'inputs', ignore=shutil.ignore_patterns('__pycache__'))
runner = (parent/'run_branches.py').read_text(encoding='utf-8')
runner = runner.replace('output_dir=call_dir, design_review_enabled=True,',
    "output_dir=call_dir, design_review_enabled=True, design_brief_schema_version='text2ifc/design-brief/2.2',")
(out/'run_branches.py').write_text(runner, encoding='utf-8', newline='\n')
prep = (parent/'prepare_admission.py').read_text(encoding='utf-8')
prep = prep.replace('versioned optional appearance removal', 'explicit semantic authority and bounded Brief repair')
prep = prep.replace("PARENT = BASE / 'projection-retry-20260910'", "PARENT = BASE / 'appearance-guard-rerun-20260910'")
prep = prep.replace('25a7dcb4706b8bf4', '4927c3df4028e515')
prep = prep.replace("'agent/test_appearance_request_projection.py']", "'agent/test_appearance_request_projection.py',\n                       'agent/test_semantic_authority_completeness.py', 'agent/test_phase6_4_issue_normalizers.py']")
prep = prep.replace("(ORIGINAL, 'FILES.json'), (PARENT, 'FILES.json')", "(ORIGINAL, 'FILES.json'), (BASE/'projection-retry-20260910', 'FILES.json'), (PARENT, 'FILES.json')")
prep = prep.replace("== 6 and all", "== 11 and all").replace("'A_prior_calls_charged':6", "'A_prior_calls_charged':11")
prep = prep.replace("ROOT/'prompts/agent/registry.json'])", """ROOT/'prompts/agent/registry.json', ROOT/'src/text2ifc_agent/brief_semantic_repair.py',
                  ROOT/'schemas/agent/design-brief/2.2/schema.json',
                  ROOT/'prompts/agent/design-brief-v2.5.md', ROOT/'prompts/agent/design-brief-v2.6.md',
                  ROOT/'prompts/agent/design-brief-semantic-repair-v1.0.md',
                  ROOT/'scripts/agent/run_phase6_2_cli.py'])""")
prep = prep.replace('.tmp/pytest-style-stage-', '.tmp/pytest-semantic-authority-stage-')
prep = prep.replace("'Generation with ChangeSet 1.1 optional appearance removal'", "'Generation with Design Brief 2.2 explicit authority and bounded semantic repair'")
prep = prep.replace('Fresh stage seams and complete offline public chain because schema and transaction permissions gained a versioned, request-bound optional-field removal.',
    'Fresh stage seams and complete offline public chain because Brief 2.2 adds mandatory semantic declarations and one scope-preserving, budgeted Agent correction.')
prep = prep.replace('Request-owned whole-product appearance gate plus narrowly authorized ChangeSet 1.1 removal. Original A offline replay restores all290 frozen IFC checks; old live QA failure unchanged.',
    'Missing extraction fails closed at Brief, cleanup and publication; explicit category review and one bounded semantic-only correction preserve frozen geometry and previous structured values. The frozen20-case diagnostic now passes; old live QA failure remains unchanged.')
prep = prep.replace("'versions_atomic_scope':'changeset1.0/1.1 contracts/application and unrequested_appearance family'",
    "'versions_atomic_scope':'Brief2.1/2.2, missing/partial/false authority, preserved semantics and geometry, malformed correction, shared budget; unchanged ChangeSet1.0/1.1 and appearance family'")
(out/'prepare_admission.py').write_text(prep, encoding='utf-8', newline='\n')
diag = out/'diagnostics'
diag.mkdir()
for source in ['semantic-authority-red-20260910.xml', 'semantic-authority-red-20260910.log',
    'brief-repair-red-20260910.xml', 'brief-repair-red-20260910.log', 'brief-public-red-20260910.xml',
    'brief-public-red-20260910.log', 'missing-request-red-20260910.xml', 'missing-request-red-20260910.log',
    'semantic-authority-frozen-replay-green-20260910.json', 'brief-failure-bounds-20260910.xml']:
    shutil.copyfile(Path('.tmp')/source, diag/source)
print(out)
