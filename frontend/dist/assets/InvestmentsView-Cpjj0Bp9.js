import{$ as e,A as t,E as n,N as r,S as i,U as a,c as o,d as s,g as c,h as l,it as u,l as d,m as f,t as p,u as m,xt as h}from"./_plugin-vue_export-helper-BJ6WweKP.js";import{it as g,l as _,o as v,t as y}from"./button-DbtICHgw.js";import{f as b,i as x,r as S}from"./index-CuWJEnuQ.js";import{n as C,r as w,t as T}from"./money-BCx50omu.js";import{n as E,t as D}from"./column-BwV81nB5.js";import{t as O}from"./tag-CbwrYg6g.js";import{t as k}from"./skeleton-BhVb4OOk.js";import{t as A}from"./PageHeader-rxFhlkHw.js";import{t as j}from"./EmptyState-Cnz5XLo5.js";var M=_.extend({name:`progressbar`,style:`
    .p-progressbar {
        display: block;
        position: relative;
        overflow: hidden;
        height: dt('progressbar.height');
        background: dt('progressbar.background');
        border-radius: dt('progressbar.border.radius');
    }

    .p-progressbar-value {
        margin: 0;
        background: dt('progressbar.value.background');
    }

    .p-progressbar-label {
        color: dt('progressbar.label.color');
        font-size: dt('progressbar.label.font.size');
        font-weight: dt('progressbar.label.font.weight');
    }

    .p-progressbar-determinate .p-progressbar-value {
        height: 100%;
        width: 0%;
        position: absolute;
        display: none;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        transition: width 1s ease-in-out;
    }

    .p-progressbar-determinate .p-progressbar-label {
        display: inline-flex;
    }

    .p-progressbar-indeterminate .p-progressbar-value::before {
        content: '';
        position: absolute;
        background: inherit;
        inset-block-start: 0;
        inset-inline-start: 0;
        inset-block-end: 0;
        will-change: inset-inline-start, inset-inline-end;
        animation: p-progressbar-indeterminate-anim 2.1s cubic-bezier(0.65, 0.815, 0.735, 0.395) infinite;
    }

    .p-progressbar-indeterminate .p-progressbar-value::after {
        content: '';
        position: absolute;
        background: inherit;
        inset-block-start: 0;
        inset-inline-start: 0;
        inset-block-end: 0;
        will-change: inset-inline-start, inset-inline-end;
        animation: p-progressbar-indeterminate-anim-short 2.1s cubic-bezier(0.165, 0.84, 0.44, 1) infinite;
        animation-delay: 1.15s;
    }

    @keyframes p-progressbar-indeterminate-anim {
        0% {
            inset-inline-start: -35%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
        100% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
    }
    @-webkit-keyframes p-progressbar-indeterminate-anim {
        0% {
            inset-inline-start: -35%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
        100% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
    }

    @keyframes p-progressbar-indeterminate-anim-short {
        0% {
            inset-inline-start: -200%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
        100% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
    }
    @-webkit-keyframes p-progressbar-indeterminate-anim-short {
        0% {
            inset-inline-start: -200%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
        100% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
    }
`,classes:{root:function(e){var t=e.instance;return[`p-progressbar p-component`,{"p-progressbar-determinate":t.determinate,"p-progressbar-indeterminate":t.indeterminate}]},value:`p-progressbar-value`,label:`p-progressbar-label`}}),N={name:`ProgressBar`,extends:{name:`BaseProgressBar`,extends:v,props:{value:{type:Number,default:null},mode:{type:String,default:`determinate`},showValue:{type:Boolean,default:!0}},style:M,provide:function(){return{$pcProgressBar:this,$parentInstance:this}}},inheritAttrs:!1,computed:{progressStyle:function(){return{width:this.value+`%`,display:`flex`}},indeterminate:function(){return this.mode===`indeterminate`},determinate:function(){return this.mode===`determinate`},dataP:function(){return g({determinate:this.determinate,indeterminate:this.indeterminate})}}},P=[`aria-valuenow`,`data-p`],F=[`data-p`],I=[`data-p`],L=[`data-p`];function R(e,n,a,o,c,l){return t(),s(`div`,i({role:`progressbar`,class:e.cx(`root`),"aria-valuemin":`0`,"aria-valuenow":e.value,"aria-valuemax":`100`,"data-p":l.dataP},e.ptmi(`root`)),[l.determinate?(t(),s(`div`,i({key:0,class:e.cx(`value`),style:l.progressStyle,"data-p":l.dataP},e.ptm(`value`)),[e.value!=null&&e.value!==0&&e.showValue?(t(),s(`div`,i({key:0,class:e.cx(`label`),"data-p":l.dataP},e.ptm(`label`)),[r(e.$slots,`default`,{},function(){return[f(h(e.value+`%`),1)]})],16,I)):m(``,!0)],16,F)):l.indeterminate?(t(),s(`div`,i({key:1,class:e.cx(`value`),"data-p":l.dataP},e.ptm(`value`)),null,16,L)):m(``,!0)],16,P)}N.render=R;var z={class:`glass panel`},B={class:`mono`},V={class:`mono success`},H={class:`muted small`},U=p(c({__name:`InvestmentsView`,setup(r){let i=b(),c=e(!0),p=e([]);return n(async()=>{try{let{data:e}=await S.investments();p.value=x(e)}finally{c.value=!1}}),(e,n)=>(t(),s(`div`,null,[l(A,{title:`My investments`,subtitle:`Active and completed positions`},{default:a(()=>[l(u(y),{label:`New investment`,icon:`pi pi-plus`,onClick:n[0]||=e=>u(i).push(`/plans`)})]),_:1}),o(`div`,z,[c.value?(t(),d(u(k),{key:0,height:`240px`})):p.value.length?(t(),d(u(E),{key:1,value:p.value,paginator:``,rows:10,"responsive-layout":`scroll`},{default:a(()=>[l(u(D),{field:`plan_name`,header:`Plan`}),l(u(D),{field:`amount`,header:`Amount`},{body:a(({data:e})=>[o(`span`,B,h(u(T)(e.amount)),1)]),_:1}),l(u(D),{field:`total_earned`,header:`Earned`},{body:a(({data:e})=>[o(`span`,V,`+`+h(u(T)(e.total_earned)),1)]),_:1}),l(u(D),{header:`Progress`},{body:a(({data:e})=>[l(u(N),{value:Math.min(100,e.progress_percent||0),style:{height:`8px`}},null,8,[`value`]),o(`div`,H,h(Math.round(e.progress_percent||0))+`%`,1)]),_:1}),l(u(D),{field:`status`,header:`Status`},{body:a(({data:e})=>[l(u(O),{value:e.status,severity:u(w)(e.status)},null,8,[`value`,`severity`])]),_:1}),l(u(D),{field:`matures_at`,header:`Matures`},{body:a(({data:e})=>[f(h(u(C)(e.matures_at)),1)]),_:1})]),_:1},8,[`value`])):(t(),d(j,{key:2,title:`No investments yet`,text:`Browse plans and put your balance to work.`},{default:a(()=>[l(u(y),{label:`Browse plans`,icon:`pi pi-chart-line`,onClick:n[1]||=e=>u(i).push(`/plans`)})]),_:1}))])]))}}),[[`__scopeId`,`data-v-044fb7fa`]]);export{U as default};