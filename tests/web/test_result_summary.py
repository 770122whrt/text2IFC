import ifcopenshell
from text2ifc_web.result_summary import summarize_operations


def test_summary_counts_products_not_relationships_and_keeps_uncompleted_operations():
    source=ifcopenshell.file(schema='IFC2X3');wall=source.create_entity('IfcWall',GlobalId=ifcopenshell.guid.new(),Name='Wall A')
    result=ifcopenshell.file.from_string(source.to_string());window=result.create_entity('IfcWindow',GlobalId=ifcopenshell.guid.new(),Name='Window 1');opening=result.create_entity('IfcOpeningElement',GlobalId=ifcopenshell.guid.new());pset=result.create_entity('IfcPropertySet',GlobalId=ifcopenshell.guid.new())
    intent={'operations':[{'operation_id':'a','operation_type':'add_window_with_opening_to_wall','target_query':{'global_id':wall.GlobalId}},{'operation_id':'b','operation_type':'add_column'}]}
    app={'operations':[{'operation_id':'a','operation_type':'add_window_with_opening_to_wall','changes':{'created':[{'global_id':x.GlobalId} for x in (window,opening,pset)],'modified':[{'global_id':wall.GlobalId}]}}]}
    summary=summarize_operations(source,result,intent,app,False)
    assert summary['operation_total']==2 and summary['published_operations']==0
    assert summary['rows'][0]['status']=='applied_not_published'
    assert len(summary['rows'][0]['created'])==1
    assert summary['rows'][0]['created'][0]['global_id']==window.GlobalId
    assert summary['rows'][1]['status']=='not_completed'
    published=summarize_operations(source,result,{'operations':intent['operations'][:1]},app,True)
    assert published['published_operations']==1 and published['rows'][0]['modified'][0]['name']=='Wall A'
