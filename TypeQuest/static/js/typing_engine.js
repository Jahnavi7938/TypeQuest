(()=>{
const passageEl=document.getElementById('passage'); if(!passageEl)return;
const input=document.getElementById('typingInput'), timeEl=document.getElementById('time');
const wpmEl=document.getElementById('wpm'),accEl=document.getElementById('accuracy'),errEl=document.getElementById('errors');
const progressEl=document.getElementById('progressLabel'),statusEl=document.getElementById('status');
const resultPanel=document.getElementById('resultPanel');
let passage=window.TYPEQUEST_PASSAGE||"Practice makes progress. Keep your focus and enjoy every new challenge.";
let duration=15,remaining=15,started=false,finished=false,interval=null,startAt=0;
let correct=0,wrong=0;
const render=()=>{
 const typed=input.value; let html='';
 for(let i=0;i<passage.length;i++){
   let cls=i<typed.length?(typed[i]===passage[i]?'correct':'incorrect'):(i===typed.length?'current':'');
   html+=`<span class="${cls}">${escapeHtml(passage[i])}</span>`;
 }
 passageEl.innerHTML=html;
};
const escapeHtml=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const metrics=()=>{
 const typed=input.value;correct=0;wrong=0;
 for(let i=0;i<typed.length;i++){if(typed[i]===passage[i])correct++;else wrong++;}
 const elapsed=started?Math.max(1,(Date.now()-startAt)/1000):0;
 const wpm=elapsed?Math.round((correct/5)/(elapsed/60)):0;
 const accuracy=typed.length?Math.round(correct/typed.length*100):100;
 wpmEl.textContent=wpm;accEl.textContent=accuracy+'%';errEl.textContent=wrong;
 progressEl.textContent=Math.min(100,Math.round(typed.length/passage.length*100))+'% completed';
 return {wpm,accuracy,elapsed};
};
const tick=()=>{remaining--;timeEl.textContent=remaining+'s';if(remaining<=0)finish();};
const start=()=>{
 if(started||finished)return;
 started=true;startAt=Date.now();statusEl.textContent='IN SESSION';
 interval=setInterval(tick,1000);
};
const finish=()=>{
 if(finished)return;finished=true;clearInterval(interval);input.disabled=true;statusEl.textContent='SESSION COMPLETE';
 const m=metrics(),elapsed=Math.max(1,Math.min(duration,Math.round(m.elapsed)));
 const cpm=Math.round(correct/(elapsed/60));
 document.getElementById('finalWpm').textContent=Math.round((correct/5)/(elapsed/60));
 document.getElementById('finalAccuracy').textContent=m.accuracy+'%';
 document.getElementById('finalCpm').textContent=cpm;
 resultPanel.classList.remove('d-none');
 const message=document.getElementById('saveMessage');
 const payload={duration,elapsed,correct_chars:correct,wrong_chars:wrong,typed_text:input.value,difficulty:document.getElementById('difficulty').value,mode:document.getElementById('mode').value};
 fetch('/api/result',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('meta[name="csrf-token"]').content},body:JSON.stringify(payload)})
 .then(async r=>{let d=await r.json();message.textContent=d.saved?'Your result has been saved to your TypeQuest profile.':(d.message||'Sign in to save this result.');})
 .catch(()=>message.textContent='Your result is shown above. Sign in to save sessions.');
};
const reset=()=>{
 clearInterval(interval);started=false;finished=false;remaining=duration;startAt=0;input.disabled=false;input.value='';
 timeEl.textContent=duration+'s';statusEl.textContent='READY WHEN YOU ARE';resultPanel.classList.add('d-none');render();metrics();input.focus();
};
input.addEventListener('input',()=>{
 if(finished)return;if(!started&&input.value.length)start();
 if(input.value.length>=passage.length){input.value=input.value.slice(0,passage.length);finish();}
 render();metrics();
});
document.getElementById('focusBtn').addEventListener('click',()=>input.focus());
document.getElementById('resetBtn').addEventListener('click',reset);
document.getElementById('againBtn').addEventListener('click',reset);
document.querySelectorAll('#durationOptions button').forEach(btn=>btn.addEventListener('click',()=>{
 document.querySelectorAll('#durationOptions button').forEach(b=>b.classList.remove('active'));btn.classList.add('active');
 duration=Number(btn.dataset.duration);reset();
}));
document.getElementById('difficulty').addEventListener('change',()=>location.href='/typing?level='+encodeURIComponent(document.getElementById('difficulty').value));
document.getElementById('mode').addEventListener('change',e=>{if(e.target.value==='words'){passage=passage.split(' ').slice(0,25).join(' ');reset();}else{location.reload();}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){input.blur();}if(e.ctrlKey&&e.key.toLowerCase()==='r'){e.preventDefault();reset();}});
render();reset();
})();
