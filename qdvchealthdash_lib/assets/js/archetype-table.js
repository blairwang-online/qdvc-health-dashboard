// ---- Archetype table ---------------------------------------------------- //
(function(){
  const tbody=document.querySelector('#archetypeTable tbody');
  if(!A.table7.length){
    tbody.innerHTML='<tr><td colspan="6" class="axis">No recent data.</td></tr>';
    return;
  }
  const pill=(txt,bg,fg)=>
    '<span class="pill" style="background:'+bg+';color:'+fg+'">'+txt+'</span>';
  const compPill=(txt,bg,fg,bi,ei)=>
    '<span class="pill persona-open" role="button" tabindex="0" '
    + 'data-bi="'+bi+'" data-ei="'+ei+'" '
    + 'style="background:'+bg+';color:'+fg+'">'+txt+'</span>';
  A.table7.forEach(r=>{
    const tr=document.createElement('tr');
    tr.innerHTML =
      '<td class="date">'+r.date+'</td>'+
      '<td class="time">'+r.begin+'</td>'+
      '<td class="time">'+r.end+'</td>'+
      '<td>'+pill(r.begin_type, r.begin_bg, r.begin_fg)+'</td>'+
      '<td>'+pill(r.end_type,   r.end_bg,   r.end_fg)+'</td>'+
      '<td>'+compPill(r.composite, r.comp_bg, r.comp_fg, r.bi, r.ei)+'</td>';
    tbody.appendChild(tr);
  });
})();

