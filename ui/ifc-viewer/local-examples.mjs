import {t,getLanguage,onLanguageChange} from './i18n.mjs';
export class LocalExamples {
 constructor({button,dialog,client,onChoose,locked,onError=console.error}){Object.assign(this,{button,dialog,client,onChoose,locked,onError,items:[]});button.onclick=()=>this.open().catch(this.onError);onLanguageChange(()=>{if(dialog.open)this.render();});}
 async open(){if(this.locked())return;this.items=(await this.client.examples()).examples;this.render();this.dialog.showModal();}
 render(){
  this.dialog.replaceChildren();const title=document.createElement('h2');title.textContent=t('demo.title');const close=document.createElement('button');close.textContent=t('action.close');close.onclick=()=>this.dialog.close();this.dialog.append(title,close);
  if(!this.items.length){const p=document.createElement('p');p.textContent=t('demo.noExamples');this.dialog.append(p);}
  for(const item of this.items){const card=document.createElement('section');card.className='example-card';const h=document.createElement('h3');h.textContent=getLanguage()==='en'?item.title_en:item.title;const p=document.createElement('p');p.textContent=item.request;const note=document.createElement('small');note.textContent=t('demo.history')+' · '+item.recorded_at.slice(0,10);card.append(h,p,note);
   for(const [mode,key] of [['input','demo.input'],['history','demo.result']]){const b=document.createElement('button');b.type='button';b.dataset.exampleId=item.id;b.dataset.exampleMode=mode;b.textContent=t(key);b.onclick=async()=>{if(this.locked())return;this.dialog.close();try{await this.onChoose(item,mode);}catch(e){console.error('EXAMPLE_LOAD_FAILED',e);}};card.append(b);}this.dialog.append(card);
  }
 }
}
