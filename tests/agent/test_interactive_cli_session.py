import json
from pathlib import Path

from text2ifc_agent.interactive_session import run_interactive_session
from text2ifc_agent.session_store import SessionStore


def test_shared_session_db_preserves_chinese_turns_and_isolates_sessions(tmp_path):
    db_path = tmp_path / "sessions.sqlite"
    store = SessionStore.open(db_path)

    first = store.create_session(original_input="创建一个长6米宽4米高3米的房间")
    second = store.create_session(original_input="再创建一个小会议室")
    store.append_turn(first.session_id, role="user", text="墙厚300mm")
    store.append_turn(second.session_id, role="user", text="我不知道窗台高度")

    assert db_path.exists()
    assert first.session_hash != second.session_hash
    assert store.get_session(first.session_id).original_input == "创建一个长6米宽4米高3米的房间"
    assert [turn.text for turn in store.list_turns(first.session_id)] == [
        "创建一个长6米宽4米高3米的房间",
        "墙厚300mm",
    ]
    assert [turn.text for turn in store.list_turns(second.session_id)] == [
        "再创建一个小会议室",
        "我不知道窗台高度",
    ]


def test_session_export_uses_db_truth_and_session_hash_run_dir(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个带门窗的房间")
    store.append_event(session.session_id, event_type="cli.status", payload={"status": "incomplete"})
    store.record_artifact(
        session.session_id,
        kind="placeholder",
        path=Path("runs") / session.session_hash / "placeholder.txt",
    )

    export_path = store.export_session(session.session_hash)
    export = json.loads(export_path.read_text(encoding="utf-8"))

    assert export_path == root / "runs" / session.session_hash / "session-export.json"
    assert export["session"]["session_id"] == session.session_id
    assert export["session"]["session_hash"] == session.session_hash
    assert export["turns"][0]["text"] == "创建一个带门窗的房间"
    assert export["events"][0]["event_type"] == "cli.status"
    assert export["artifacts"][0]["kind"] == "placeholder"


def test_session_export_records_the_export_artifact_in_payload(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个房间")

    export_path = store.export_session(session.session_hash)
    export = json.loads(export_path.read_text(encoding="utf-8"))

    assert export["artifacts"] == [
        {
            "kind": "session_export",
            "path": str(Path("runs") / session.session_hash / "session-export.json"),
            "created_at": export["artifacts"][0]["created_at"],
        }
    ]


def test_dry_run_cli_scripted_stdin_creates_incomplete_queryable_session(tmp_path):
    from scripts.agent import run_phase6_2_cli

    root = tmp_path / "phase6.2-interactive-cli"
    scripted_stdin = tmp_path / "session-smoke.stdin"
    scripted_stdin.write_text(
        "\n".join(
            [
                "创建一个长6米、宽4米、高3米的房间，南墙有门，北墙有窗。",
                "status",
                "quit",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = run_phase6_2_cli.main(
        [
            "--db",
            str(root / "sessions.sqlite"),
            "--output-root",
            str(root),
            "--scripted-stdin",
            str(scripted_stdin),
            "--dry-run",
        ]
    )
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    sessions = store.list_sessions()

    assert exit_code == 0
    assert len(sessions) == 1
    assert sessions[0].status == "incomplete"
    assert sessions[0].original_input.startswith("创建一个长6米")
    assert (root / "runs" / sessions[0].session_hash).is_dir()


def test_query_cli_lists_shows_turns_and_exports_session(tmp_path, capsys):
    from scripts.agent import query_phase6_2_sessions

    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个办公室")
    store.append_turn(session.session_id, role="user", text="墙厚300mm")

    assert query_phase6_2_sessions.main(["--db", str(root / "sessions.sqlite"), "list"]) == 0
    list_output = capsys.readouterr().out
    assert session.session_hash in list_output

    assert (
        query_phase6_2_sessions.main(
            ["--db", str(root / "sessions.sqlite"), "show", session.session_hash]
        )
        == 0
    )
    show_output = json.loads(capsys.readouterr().out)
    assert show_output["session_hash"] == session.session_hash

    assert (
        query_phase6_2_sessions.main(
            ["--db", str(root / "sessions.sqlite"), "turns", session.session_hash]
        )
        == 0
    )
    turns_output = json.loads(capsys.readouterr().out)
    assert [turn["text"] for turn in turns_output] == ["创建一个办公室", "墙厚300mm"]

    assert (
        query_phase6_2_sessions.main(
            [
                "--db",
                str(root / "sessions.sqlite"),
                "--output-root",
                str(root),
                "export",
                session.session_hash,
            ]
        )
        == 0
    )
    export_output = json.loads(capsys.readouterr().out)
    assert Path(export_output["export_path"]).is_file()


def test_interactive_session_resume_appends_to_existing_hash(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个房间")

    result = run_interactive_session(
        store=store,
        input_lines=["status", "quit"],
        dry_run=True,
        resume=session.session_hash,
    )

    assert result.session_hash == session.session_hash
    assert store.get_session(session.session_hash).status == "incomplete"
    assert [event.event_type for event in store.list_events(session.session_id)] == [
        "cli.status",
        "cli.quit",
    ]
