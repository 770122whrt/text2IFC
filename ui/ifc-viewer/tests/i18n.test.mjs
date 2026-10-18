import test, {afterEach} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {catalogs,t,getLanguage,setLanguage,readLanguage,onLanguageChange,uiError,errorText} from '../i18n.mjs';
import {formatValue,propertyGroups} from '../inspection-data.mjs';

afterEach(()=>setLanguage('zh',{persist:false}));
test('both languages have identical keys and interpolation arguments',()=>{
 assert.deepEqual(Object.keys(catalogs.zh).sort(),Object.keys(catalogs.en).sort());
 const args=s=>[...s.matchAll(/\{(\w+)\}/g)].map(x=>x[1]).sort();
 for(const key of Object.keys(catalogs.zh)){assert.ok(catalogs.en[key].trim(),key);assert.deepEqual(args(catalogs.zh[key]),args(catalogs.en[key]),key);}
});
test('switching changes UI wording, not injected source strings',()=>{
 setLanguage('en',{persist:false});assert.equal(t('action.open'),'Open IFC');
 const name='中文墙体 <script>source</script>';
 assert.ok(t('error.open',{name,error:'raw parser detail'}).includes(name));
 assert.equal(t('display.hiddenCount',{count:7}),'Hidden: 7');
 setLanguage('zh',{persist:false});assert.equal(t('action.open'),'打开 IFC');
});
test('locale preference tolerates blocked storage and invalid values',()=>{
 assert.equal(readLanguage({getItem:()=>{throw Error('blocked');}}),'zh');
 assert.equal(readLanguage({getItem:()=> 'not-a-language'}),'zh');
 assert.equal(readLanguage({getItem:()=> 'en'}),'en');
 assert.doesNotThrow(()=>setLanguage('en',{storage:{setItem:()=>{throw Error('blocked');}}}));assert.equal(getLanguage(),'en');
});
test('locale notifications do not require a DOM or reload',()=>{
 let calls=0;const off=onLanguageChange(()=>calls++);
 setLanguage('en',{persist:false});setLanguage('en',{persist:false});assert.equal(calls,1);off();
 setLanguage('zh',{persist:false});assert.equal(calls,1);
});
test('source-valued property labels, numbers and units are never translated',()=>{
 const input=[{Name:{value:'Pset_墙体'},HasProperties:[{Name:{value:'LoadBearing'},NominalValue:{value:false}},{Name:{value:'长度'},NominalValue:{value:0,name:'IFCLENGTHMEASURE'}}]}];
 const before=JSON.stringify(input);setLanguage('en',{persist:false});
 const g=propertyGroups(input,{LENGTHUNIT:'mm'});assert.equal(g[0].name,'Pset_墙体');assert.equal(g[0].rows[0].name,'LoadBearing');assert.equal(g[0].rows[0].value,'No');assert.equal(g[0].rows[1].value,'0');assert.equal(g[0].rows[1].unit,'mm');assert.equal(JSON.stringify(input),before);
 assert.equal(formatValue({value:'否',name:'IFCLABEL'}),'否');assert.equal(formatValue(null),'Not recorded');
 assert.equal(formatValue({value:'UNKNOWN',label:'IfcLogical'}),'Unknown');
 setLanguage('zh',{persist:false});assert.equal(formatValue({value:false}),'否');
});
test('UI errors are re-renderable while unknown parser details remain raw',()=>{
 const e=uiError('error.notStep');setLanguage('en',{persist:false});assert.equal(errorText(e),'The file is not valid IFC STEP text.');
 assert.equal(errorText(Error('raw kernel error 中文')),'raw kernel error 中文');
 assert.equal(errorText(Error('请先描述修改需求')),'Enter a modification request first.');
});
test('static translation attributes reference real keys and never target editable inputs as text',()=>{
 const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
 for(const match of html.matchAll(/data-i18n(?:-title|-aria-label|-placeholder)?="([^"]+)"/g))assert.ok(catalogs.en[match[1]],match[1]);
 assert.match(html,/id="langEn"/);assert.match(html,/id="langZh"/);
 assert.doesNotMatch(html,/<textarea[^>]*\sdata-i18n="/);
});
