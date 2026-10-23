(() => {
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];
  const state = { tool: null, files: [], category: "all" };
  const toolInfo = {
    merge:{title:"Merge PDF",description:"Combine two or more PDF files into one document.",label:"Output filename",placeholder:"merged-document.pdf",help:"Select at least two PDF files. Their current order is preserved.",accept:".pdf",multiple:true},
    split:{title:"Split PDF",description:"Extract one page from a PDF into a separate document.",label:"Page number",placeholder:"1",help:"This starter extracts one page per run. Page numbers start at 1.",accept:".pdf",multiple:false},
    compress:{title:"Compress PDF",description:"Re-save a PDF with a normalized structure.",label:"Output filename",placeholder:"optimized.pdf",help:"PDF re-saving does not guarantee a smaller file; deep image compression is not included yet.",accept:".pdf",multiple:false},
    rotate:{title:"Rotate PDF",description:"Rotate all pages clockwise by 90 degrees.",label:"Output filename",placeholder:"rotated.pdf",help:"All pages are rotated clockwise by 90 degrees.",accept:".pdf",multiple:false},
    watermark:{title:"Watermark PDF",description:"Stamp text across every page of your PDF.",label:"Watermark text",placeholder:"CONFIDENTIAL",help:"Text is added diagonally near the center of each page.",accept:".pdf",multiple:false},
    "jpg-to-pdf":{title:"JPG to PDF",description:"Create a PDF from JPG, PNG, or WebP images.",label:"Output filename",placeholder:"images.pdf",help:"Images are added in the order shown below. PNG and JPG are supported directly; WebP support depends on browser decoding.",accept:".jpg,.jpeg,.png,.webp",multiple:true},
    "pdf-to-jpg":{title:"PDF to JPG",description:"Export PDF pages as images.",label:"Export note",placeholder:"PDF page rendering is not enabled in this starter",help:"Requires PDF.js rendering and ZIP export, planned for a future release.",accept:".pdf",multiple:false},
    protect:{title:"Protect PDF",description:"Add password encryption to a PDF.",label:"Password",placeholder:"Password encryption engine not configured",help:"The current browser library does not provide PDF encryption. This operation is not implemented.",accept:".pdf",multiple:false},
    unlock:{title:"Unlock PDF",description:"Open a PDF you are authorized to access.",label:"Password",placeholder:"Enter the document password",help:"Password removal is only available for files you own or are authorized to modify. Encrypted PDF support is limited.",accept:".pdf",multiple:false},
    organize:{title:"Organize pages",description:"Inspect the PDF and prepare page reordering.",label:"Feature status",placeholder:"Page-thumbnail editor planned",help:"Interactive page thumbnails and drag-to-reorder are planned, not yet implemented.",accept:".pdf",multiple:false},
    "page-numbers":{title:"Page numbers",description:"Add page numbers to every page.",label:"Starting number",placeholder:"1",help:"Numbers are added at the bottom center of each page.",accept:".pdf",multiple:false},
    edit:{title:"Edit PDF",description:"Add text and graphics to existing PDF pages.",label:"Feature status",placeholder:"Full visual editor planned",help:"The visual editor is not implemented in this initial release.",accept:".pdf",multiple:false}
  };
  const bytes = (n) => n < 1024 ? n+" B" : n < 1048576 ? (n/1024).toFixed(1)+" KB" : (n/1048576).toFixed(2)+" MB";
  const safeName = (s, fallback) => {
    let v = (s || fallback).trim().replace(/[\\/:*?"<>|]+/g,"-");
    if (!v.toLowerCase().endsWith(".pdf")) v += ".pdf";
    return v;
  };
  let toastTimer;
  function toast(message){const el=$("#toast");el.textContent=message;el.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove("show"),2800);}
  function setStatus(message){$("#statusText").textContent=message;}
  function setTool(name){
    state.tool=name;
    const info=toolInfo[name];
    $$(".tool-card").forEach(c=>c.classList.toggle("selected",c.dataset.tool===name));
    $("#workspaceTitle").textContent=info.title;
    $("#workspaceDescription").textContent=info.description;
    $("#fileInput").accept=info.accept;
    $("#fileInput").multiple=info.multiple;
    $("#optionLabel").textContent=info.label;
    $("#toolOption").placeholder=info.placeholder;
    $("#toolOption").value="";
    $("#optionHelp").textContent=info.help;
    $("#optionsPanel").classList.remove("hidden");
    $("#resultPanel").classList.add("hidden");
    renderFiles();
    $("#processButton").textContent=info.title+" →";
    validate();
    $("#workspace").scrollIntoView({behavior:"smooth",block:"start"});
  }
  function addFiles(list){
    const incoming=[...list];
    if(!incoming.length)return;
    if(!state.tool){setTool(incoming[0].type.startsWith("image/")?"jpg-to-pdf":"merge");}
    const info=toolInfo[state.tool];
    let accepted=incoming.filter(f=>{
      const ext="."+f.name.split(".").pop().toLowerCase();
      return info.accept.split(",").some(a=>a.trim()===ext) || (f.type==="application/pdf"&&info.accept.includes(".pdf"));
    });
    if(!info.multiple) accepted=accepted.slice(0,1);
    if(!accepted.length){toast("This tool does not support the selected file type.");return;}
    const existing=state.files;
    state.files=info.multiple?[...existing,...accepted]:accepted;
    renderFiles();validate();$("#resultPanel").classList.add("hidden");
  }
  function renderFiles(){
    const list=$("#fileList");list.innerHTML="";
    state.files.forEach((file,i)=>{
      const row=document.createElement("div");row.className="file-row";
      const badge=document.createElement("div");badge.className="file-pdf";badge.textContent=file.name.toLowerCase().endsWith(".pdf")?"PDF":"IMG";
      const info=document.createElement("div");info.className="file-info";
      const name=document.createElement("strong");name.textContent=file.name;
      const size=document.createElement("small");size.textContent=bytes(file.size);
      info.append(name,size);
      const remove=document.createElement("button");remove.className="remove-file";remove.type="button";remove.setAttribute("aria-label","Remove "+file.name);remove.textContent="×";remove.onclick=()=>{state.files.splice(i,1);renderFiles();validate();};
      row.append(badge,info,remove);list.append(row);
    });
  }
  function validate(){
    const t=state.tool;
    const count=state.files.length;
    let needed=t==="merge"?2:1;
    const implemented=["merge","split","compress","rotate","watermark","jpg-to-pdf","pdf-to-jpg","page-numbers"];
    const can=t&&count>=needed&&implemented.includes(t);
    $("#processButton").disabled=!can;
    if(!t)setStatus("Ready when you are");
    else if(count<needed)setStatus("Add "+(needed-count)+" more file"+(needed-count===1?"":"s"));
    else if(!implemented.includes(t))setStatus("This tool is on the roadmap");
    else setStatus(count+" file"+(count===1?"":"s")+" ready to process");
  }
  async function loadPdf(file){return PDFLib.PDFDocument.load(await file.arrayBuffer());}
  function downloadBlob(blob,name){
    const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);
  }
  async function processTool(){
    const t=state.tool;const info=toolInfo[t];const opt=$("#toolOption").value.trim();
    if(!t||!state.files.length)return;
    if(["protect","unlock","organize","edit"].includes(t)){toast("This tool is not implemented yet. See the roadmap in README.");return;}
    const btn=$("#processButton");btn.disabled=true;btn.textContent="Processing…";setStatus("Processing files locally…");$("#resultPanel").classList.add("hidden");
    try{
      let out,name,outputType="application/pdf";
      if(t==="merge"){
        const merged=await PDFLib.PDFDocument.create();
        for(const file of state.files){const pdf=await loadPdf(file);const pages=await merged.copyPages(pdf,pdf.getPageIndices());pages.forEach(p=>merged.addPage(p));}
        out=await merged.save();name=safeName(opt,"merged.pdf");
      }else if(t==="split"){
        const pdf=await loadPdf(state.files[0]);const pageNo=Number(opt||1);
        if(!Number.isInteger(pageNo)||pageNo<1||pageNo>pdf.getPageCount())throw new Error("Enter a page number between 1 and "+pdf.getPageCount()+".");
        const doc=await PDFLib.PDFDocument.create();const [page]=await doc.copyPages(pdf,[pageNo-1]);doc.addPage(page);out=await doc.save();name=state.files[0].name.replace(/\.pdf$/i,"")+"-page-"+pageNo+".pdf";
      }else if(t==="pdf-to-jpg"){
        if(!window.pdfjsLib||!window.JSZip)throw new Error("PDF-to-JPG libraries did not load. Check your internet connection.");
        pdfjsLib.GlobalWorkerOptions.workerSrc="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
        const pdf=await pdfjsLib.getDocument({data:await state.files[0].arrayBuffer()}).promise;
        const zip=new JSZip();
        for(let i=1;i<=pdf.numPages;i++){
          setStatus("Rendering page "+i+" of "+pdf.numPages+"…");
          const page=await pdf.getPage(i);const viewport=page.getViewport({scale:1.5});
          const canvas=document.createElement("canvas");canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);
          await page.render({canvasContext:canvas.getContext("2d"),viewport}).promise;
          const blob=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error("Could not export page "+i)),"image/jpeg",.9));
          zip.file("page-"+String(i).padStart(3,"0")+".jpg",blob);canvas.width=0;canvas.height=0;
        }
        out=await zip.generateAsync({type:"uint8array"});name=state.files[0].name.replace(/\\.pdf$/i,"")+"-images.zip";outputType="application/zip";
      }else if(t==="compress"){
        const pdf=await loadPdf(state.files[0]);out=await pdf.save({useObjectStreams:true});name=safeName(opt,"optimized.pdf");
      }else if(t==="rotate"){
        const pdf=await loadPdf(state.files[0]);pdf.getPages().forEach(p=>p.setRotation(PDFLib.degrees((p.getRotation().angle+90)%360)));out=await pdf.save();name=safeName(opt,"rotated.pdf");
      }else if(t==="watermark"){
        if(!opt)throw new Error("Enter the watermark text first.");
        const pdf=await loadPdf(state.files[0]);pdf.getPages().forEach(p=>{const {width,height}=p.getSize();p.drawText(opt,{x:width*.12,y:height*.48,size:28,color:PDFLib.rgb(.85,.18,.16),opacity:.28,rotate:PDFLib.degrees(35),maxWidth:width*.78});});out=await pdf.save();name=state.files[0].name.replace(/\.pdf$/i,"")+"-watermarked.pdf";
      }else if(t==="jpg-to-pdf"){
        const pdf=await PDFLib.PDFDocument.create();
        for(const file of state.files){const data=await file.arrayBuffer();let img;const ext=file.name.split(".").pop().toLowerCase();if(ext==="jpg"||ext==="jpeg")img=await pdf.embedJpg(data);else if(ext==="png")img=await pdf.embedPng(data);else{const bitmap=await createImageBitmap(file);const canvas=document.createElement("canvas");canvas.width=bitmap.width;canvas.height=bitmap.height;canvas.getContext("2d").drawImage(bitmap,0,0);const blob=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error("Could not decode image")),"image/png"));img=await pdf.embedPng(await blob.arrayBuffer());bitmap.close();}
          const scale=Math.min(595/img.width,842/img.height,1);const w=img.width*scale,h=img.height*scale;const page=pdf.addPage([w+48,h+48]);page.drawImage(img,{x:24,y:24,width:w,height:h});}
        out=await pdf.save();name=safeName(opt,"images.pdf");
      }else if(t==="page-numbers"){
        const pdf=await loadPdf(state.files[0]);const start=Number(opt||1);if(!Number.isInteger(start)||start<0)throw new Error("Enter a valid starting number.");
        pdf.getPages().forEach((p,i)=>{const {width}=p.getSize();p.drawText(String(start+i),{x:width/2-5,y:18,size:10,color:PDFLib.rgb(.25,.25,.3)});});out=await pdf.save();name=state.files[0].name.replace(/\.pdf$/i,"")+"-numbered.pdf";
      }
      const blob=new Blob([out],{type:outputType});downloadBlob(blob,name);
      const panel=$("#resultPanel");panel.classList.remove("hidden");panel.textContent="✓ Done! "+name+" · "+bytes(blob.size)+" · Your file was processed in this browser.";
      setStatus("Finished successfully");toast("Your PDF is ready to save.");
    }catch(err){console.error(err);toast(err.message||"Could not process this file.");setStatus("Processing failed");}
    finally{btn.disabled=false;btn.textContent=(toolInfo[state.tool]?.title||"Process")+" →";validate();}
  }
  $$(".tool-card").forEach(card=>card.addEventListener("click",()=>setTool(card.dataset.tool)));
  $$(".category-tab").forEach(tab=>tab.addEventListener("click",()=>{$$(".category-tab").forEach(t=>t.classList.toggle("active",t===tab));state.category=tab.dataset.category;filterTools();}));
  $("#toolSearch").addEventListener("input",filterTools);
  function filterTools(){const q=$("#toolSearch").value.toLowerCase();let shown=0;$$(".tool-card").forEach(c=>{const visible=(state.category==="all"||c.dataset.category===state.category)&&c.innerText.toLowerCase().includes(q);c.classList.toggle("hidden",!visible);if(visible)shown++;});$("#emptySearch").classList.toggle("hidden",shown>0);}
  $("#browseFiles").addEventListener("click",()=>$("#fileInput").click());
  $("#fileInput").addEventListener("change",e=>{addFiles(e.target.files);e.target.value="";});
  $("#processButton").addEventListener("click",processTool);
  const dz=$("#dropzone");["dragenter","dragover"].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.add("dragging");}));["dragleave","drop"].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.remove("dragging");}));dz.addEventListener("drop",e=>addFiles(e.dataTransfer.files));
  $("#themeToggle").addEventListener("click",()=>{document.body.classList.toggle("dark");const dark=document.body.classList.contains("dark");$("#themeToggle").textContent=dark?"☀":"☾";try{localStorage.setItem("ihp-theme",dark?"dark":"light");}catch{}});
  try{if(localStorage.getItem("ihp-theme")==="dark"){document.body.classList.add("dark");$("#themeToggle").textContent="☀";}}catch{}
  $("#mobileMenu").addEventListener("click",()=>$(".desktop-nav").classList.toggle("open"));
  $("#toolOption").addEventListener("keydown",e=>{if(e.key==="Enter"&&!$("#processButton").disabled)processTool();});
})();