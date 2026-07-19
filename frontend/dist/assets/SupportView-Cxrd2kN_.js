import{$ as e,A as t,C as n,Ct as r,E as i,F as a,H as o,M as s,O as ee,S as c,U as te,W as l,bt as u,c as d,d as f,g as p,h as m,i as h,it as g,m as _,s as v,t as y,u as b}from"./_plugin-vue_export-helper-BnoIuITy.js";import{Z as x,r as S}from"./basecomponent-Dbv6nt4q.js";import{E as C,a as w,h as ne,i as re,m as ie,n as ae,p as oe,r as T,s as E}from"./index-D5wv0lAS.js";import{t as se}from"./select-DFAjC9xd.js";import{n as D,t as O}from"./inputtext-CDm6U5-K.js";import{i as ce,r as le}from"./money-D_sYmORa.js";import{t as ue}from"./tag-CRT_n1fE.js";import{n as k,r as de,t as fe}from"./linkify-NhlMpGzm.js";var A=S.extend({name:`textarea`,style:`
    .p-textarea {
        font-family: inherit;
        font-feature-settings: inherit;
        font-size: 1rem;
        color: dt('textarea.color');
        background: dt('textarea.background');
        padding-block: dt('textarea.padding.y');
        padding-inline: dt('textarea.padding.x');
        border: 1px solid dt('textarea.border.color');
        transition:
            background dt('textarea.transition.duration'),
            color dt('textarea.transition.duration'),
            border-color dt('textarea.transition.duration'),
            outline-color dt('textarea.transition.duration'),
            box-shadow dt('textarea.transition.duration');
        appearance: none;
        border-radius: dt('textarea.border.radius');
        outline-color: transparent;
        box-shadow: dt('textarea.shadow');
    }

    .p-textarea:enabled:hover {
        border-color: dt('textarea.hover.border.color');
    }

    .p-textarea:enabled:focus {
        border-color: dt('textarea.focus.border.color');
        box-shadow: dt('textarea.focus.ring.shadow');
        outline: dt('textarea.focus.ring.width') dt('textarea.focus.ring.style') dt('textarea.focus.ring.color');
        outline-offset: dt('textarea.focus.ring.offset');
    }

    .p-textarea.p-invalid {
        border-color: dt('textarea.invalid.border.color');
    }

    .p-textarea.p-variant-filled {
        background: dt('textarea.filled.background');
    }

    .p-textarea.p-variant-filled:enabled:hover {
        background: dt('textarea.filled.hover.background');
    }

    .p-textarea.p-variant-filled:enabled:focus {
        background: dt('textarea.filled.focus.background');
    }

    .p-textarea:disabled {
        opacity: 1;
        background: dt('textarea.disabled.background');
        color: dt('textarea.disabled.color');
    }

    .p-textarea::placeholder {
        color: dt('textarea.placeholder.color');
    }

    .p-textarea.p-invalid::placeholder {
        color: dt('textarea.invalid.placeholder.color');
    }

    .p-textarea-fluid {
        width: 100%;
    }

    .p-textarea-resizable {
        overflow: hidden;
        resize: none;
    }

    .p-textarea-sm {
        font-size: dt('textarea.sm.font.size');
        padding-block: dt('textarea.sm.padding.y');
        padding-inline: dt('textarea.sm.padding.x');
    }

    .p-textarea-lg {
        font-size: dt('textarea.lg.font.size');
        padding-block: dt('textarea.lg.padding.y');
        padding-inline: dt('textarea.lg.padding.x');
    }
`,classes:{root:function(e){var t=e.instance,n=e.props;return[`p-textarea p-component`,{"p-filled":t.$filled,"p-textarea-resizable ":n.autoResize,"p-textarea-sm p-inputfield-sm":n.size===`small`,"p-textarea-lg p-inputfield-lg":n.size===`large`,"p-invalid":t.$invalid,"p-variant-filled":t.$variant===`filled`,"p-textarea-fluid":t.$fluid}]}}}),j={name:`BaseTextarea`,extends:D,props:{autoResize:Boolean},style:A,provide:function(){return{$pcTextarea:this,$parentInstance:this}}};function M(e){"@babel/helpers - typeof";return M=typeof Symbol==`function`&&typeof Symbol.iterator==`symbol`?function(e){return typeof e}:function(e){return e&&typeof Symbol==`function`&&e.constructor===Symbol&&e!==Symbol.prototype?`symbol`:typeof e},M(e)}function N(e,t,n){return(t=P(t))in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function P(e){var t=F(e,`string`);return M(t)==`symbol`?t:t+``}function F(e,t){if(M(e)!=`object`||!e)return e;var n=e[Symbol.toPrimitive];if(n!==void 0){var r=n.call(e,t);if(M(r)!=`object`)return r;throw TypeError(`@@toPrimitive must return a primitive value.`)}return(t===`string`?String:Number)(e)}var I={name:`Textarea`,extends:j,inheritAttrs:!1,observer:null,mounted:function(){var e=this;this.autoResize&&(this.observer=new ResizeObserver(function(){requestAnimationFrame(function(){e.resize()})}),this.observer.observe(this.$el))},updated:function(){this.autoResize&&this.resize()},beforeUnmount:function(){this.observer&&this.observer.disconnect()},methods:{resize:function(){if(this.$el.offsetParent){var e=this.$el.style.height,t=parseInt(e)||0,n=this.$el.scrollHeight;t&&n<t?(this.$el.style.height=`auto`,this.$el.style.height=`${this.$el.scrollHeight}px`):(!t||n>t)&&(this.$el.style.height=`${n}px`)}},onInput:function(e){this.autoResize&&this.resize(),this.writeValue(e.target.value,e)}},computed:{attrs:function(){return c(this.ptmi(`root`,{context:{filled:this.$filled,disabled:this.disabled}}),this.formField)},dataP:function(){return x(N({invalid:this.$invalid,fluid:this.$fluid,filled:this.$variant===`filled`},this.size,this.size))}}},L=[`value`,`name`,`disabled`,`aria-invalid`,`data-p`];function R(e,n,r,i,a,o){return t(),f(`textarea`,c({class:e.cx(`root`),value:e.d_value,name:e.name,disabled:e.disabled,"aria-invalid":e.invalid||void 0,"data-p":o.dataP,onInput:n[0]||=function(){return o.onInput&&o.onInput.apply(o,arguments)}},o.attrs),null,16,L)}I.render=R;var z={class:`wa-sidebar`},B={class:`wa-side-head`},V={class:`wa-search`},pe={class:`wa-chat-list`},me={key:0,class:`wa-empty-side muted`},he={key:1,class:`wa-empty-side`},ge=[`onClick`],_e={class:`wa-avatar support`},ve={class:`wa-row-body`},ye={class:`wa-row-top`},be={class:`truncate`},xe={class:`wa-time`},Se={class:`wa-row-bot`},Ce={class:`wa-preview truncate`},we={class:`wa-pane`},Te={class:`wa-chat-head`},Ee={class:`wa-chat-meta`},De={class:`truncate`},Oe={key:0,class:`dot-online`},ke={class:`wa-day-pill`},Ae={class:`wa-bubble`},je={key:0,class:`wa-sender`},Me=[`innerHTML`],Ne={class:`wa-meta`},Pe=[`title`],Fe={key:0,class:`pi pi-clock`},Ie={key:1,class:`pi pi-check`},Le={key:1,class:`fail-hint`},Re={key:0,class:`wa-bubble-row theirs typing-row`},ze={key:1,class:`wa-empty-msgs muted`},Be={key:0,class:`wa-composer`},Ve={key:1,class:`wa-composer closed`},He={key:1,class:`wa-placeholder`},Ue={class:`wa-placeholder-card`},We={key:0,class:`wa-you muted`},Ge={class:`form`},H=y(p({__name:`SupportView`,setup(c){let p=ie(),y=ne(),x=oe(),S=ae(),D=e(!0),A=e([]),j=e(null),M=e(null),N=e([]),P=e(!1),F=e(``),L=e(!1),R=e(!1),H=e(!1),U=e(``),W=e(null),G=e({subject:``,body:``,category:`general`}),K=de({isStaff:!1,onMessage:async()=>{await Z()}}),Ke=[{label:`General`,value:`general`},{label:`Deposit`,value:`deposit`},{label:`Withdrawal`,value:`withdrawal`},{label:`Investment`,value:`investment`},{label:`Account`,value:`account`},{label:`KYC`,value:`kyc`},{label:`Technical`,value:`technical`}],q=v(()=>{let e=U.value.trim().toLowerCase();return e?A.value.filter(t=>t.subject.toLowerCase().includes(e)||t.category.toLowerCase().includes(e)||t.status.toLowerCase().includes(e)):A.value}),J=v(()=>{let e=(M.value?.status||``).toLowerCase();return!!M.value&&![`closed`,`resolved`].includes(e)});function qe(e){if(!e)return``;try{let t=new Date(e),n=Math.floor((Date.now()-t.getTime())/1e3);if(n<45)return`just now`;if(n<3600)return`${Math.max(1,Math.floor(n/60))} min ago`;if(n<86400){let e=Math.floor(n/3600);return`${e} hour${e===1?``:`s`} ago`}return Y(e)}catch{return Y(e)}}let Je=v(()=>K.peerTypingText.value?K.peerTypingText.value:K.presence.value.staff_online?`online`:K.presence.value.staff_last_seen?`last seen ${qe(K.presence.value.staff_last_seen)}`:M.value?`${M.value.category} · support chat`:``),Ye=v(()=>K.connected.value?K.mode.value===`ws`?`Live`:`Live · sync`:`Connecting…`);function Xe(e){let t=e.messages||[];if(!t.length)return`No messages yet`;let n=t[t.length-1],r=n.is_staff_reply?`Support`:`You`,i=(n.body||``).replace(/\s+/g,` `).trim();return`${r}: ${i.slice(0,72)}${i.length>72?`…`:``}`}function Ze(e){let t=e.trim().split(/\s+/).filter(Boolean);return t.length?t.length===1?t[0].slice(0,2).toUpperCase():(t[0][0]+t[1][0]).toUpperCase():`S`}function Y(e){if(!e)return``;try{let t=new Date(e),n=new Date;return t.getFullYear()===n.getFullYear()&&t.getMonth()===n.getMonth()&&t.getDate()===n.getDate()?t.toLocaleTimeString(void 0,{hour:`2-digit`,minute:`2-digit`}):t.toLocaleDateString(void 0,{month:`short`,day:`numeric`})}catch{return le(e)}}function X(e){if(!e)return``;try{return new Date(e).toLocaleTimeString(void 0,{hour:`2-digit`,minute:`2-digit`})}catch{return``}}function Qe(e){let t=k(e);return t===`pending`?`Sending…`:t===`read`?`Read`:t===`delivered`?`Delivered`:`Sent`}async function Z(e=!1){await n();let t=W.value;if(!t)return;let r=t.scrollHeight-t.scrollTop-t.clientHeight<120;(e||r)&&(t.scrollTop=t.scrollHeight)}async function $e(){D.value=!0;try{let{data:e}=await T.tickets();A.value=re(e)}finally{D.value=!1}}async function Q(e,t=!1){if(e){j.value=e,t?y.replace(`/support/${e}`):p.params.id!==e&&y.push(`/support/${e}`),P.value=!0;try{let{data:t}=await T.ticket(e);M.value=t,N.value=[...t.messages||[]];let n=A.value.findIndex(t=>t.id===e);n>=0?A.value[n]={...A.value[n],...t}:A.value=[t,...A.value],K.join(e,N),K.markRead(),await Z(!0)}catch{x.toast(`Not found`,`Conversation not found`,`error`),M.value=null,j.value=null,K.leave(),y.replace(`/support`)}finally{P.value=!1}}}function et(){K.leave(),j.value=null,M.value=null,N.value=[],y.push(`/support`)}async function $(){if(!F.value.trim()||!M.value||!J.value||L.value)return;let e=F.value.trim();F.value=``,K.sendTyping(!1),L.value=!0;let t=`tmp-${Date.now()}`,n={id:t,body:e,is_staff_reply:!1,created_at:new Date().toISOString(),sender:S.user?.id||0,sender_name:S.displayName,receipt_status:`pending`,_pending:!0};N.value.push(n),await Z(!0);try{let{data:n}=await T.replyTicket(M.value.id,e),r=n,i=N.value.findIndex(e=>e.id===t);i>=0?N.value[i]={...r,_pending:!1}:K.mergeMessage(r),M.value.updated_at=r.created_at||new Date().toISOString();let a=A.value.findIndex(e=>e.id===M.value.id);a>=0&&(A.value[a]={...A.value[a],messages:N.value,updated_at:M.value.updated_at}),await Z(!0)}catch(e){let n=N.value.findIndex(e=>e.id===t);n>=0&&(N.value[n]={...N.value[n],_pending:!1,_failed:!0}),x.toast(`Failed`,e?.response?.data?.detail||`Could not send`,`error`)}finally{L.value=!1}}async function tt(){if(!G.value.subject.trim()||!G.value.body.trim()){x.toast(`Required`,`Subject and message are required`,`warn`);return}H.value=!0;try{let{data:e}=await T.createTicket(G.value);x.toast(`Started`,`Conversation opened with support`,`success`),R.value=!1,G.value={subject:``,body:``,category:`general`},A.value=[e,...A.value.filter(t=>t.id!==e.id)],await Q(e.id,!0)}catch(e){x.toast(`Failed`,e?.response?.data?.detail||`Could not create ticket`,`error`)}finally{H.value=!1}}function nt(e){e.key===`Enter`&&!e.shiftKey&&(e.preventDefault(),$())}function rt(){K.onComposerInput()}return o(()=>p.params.id,e=>{typeof e==`string`&&e?j.value!==e&&Q(e,!0):(K.leave(),j.value=null,M.value=null,N.value=[])}),i(async()=>{await $e();let e=p.params.id;typeof e==`string`&&e&&await Q(e,!0)}),ee(()=>K.leave()),(e,n)=>{let i=a(`tooltip`);return t(),f(`div`,{class:u([`wa-shell`,{"has-chat":!!j.value}])},[d(`aside`,z,[d(`header`,B,[n[10]||=d(`div`,{class:`wa-side-title`},[d(`span`,{class:`wa-brand-dot`}),d(`div`,null,[d(`h1`,null,`Support`),d(`p`,{class:`muted`},`Chat with our team`)])],-1),l(m(g(E),{icon:`pi pi-plus`,rounded:``,severity:`success`,"aria-label":`New chat`,onClick:n[0]||=e=>R.value=!0},null,512),[[i,`New chat`,void 0,{bottom:!0}]])]),d(`div`,V,[n[11]||=d(`i`,{class:`pi pi-search`},null,-1),l(d(`input`,{"onUpdate:modelValue":n[1]||=e=>U.value=e,type:`search`,placeholder:`Search chats`},null,512),[[C,U.value]])]),d(`div`,pe,[D.value?(t(),f(`div`,me,`Loading chats…`)):q.value.length?b(``,!0):(t(),f(`div`,he,[n[12]||=d(`i`,{class:`pi pi-comments`},null,-1),n[13]||=d(`p`,null,`No conversations yet`,-1),m(g(E),{label:`Start a chat`,icon:`pi pi-plus`,size:`small`,onClick:n[2]||=e=>R.value=!0})])),(t(!0),f(h,null,s(q.value,e=>(t(),f(`button`,{key:e.id,type:`button`,class:u([`wa-chat-row`,{active:j.value===e.id}]),onClick:t=>Q(e.id)},[d(`span`,_e,r(Ze(e.subject)),1),d(`span`,ve,[d(`span`,ye,[d(`strong`,be,r(e.subject),1),d(`span`,xe,r(Y(e.updated_at)),1)]),d(`span`,Se,[d(`span`,Ce,r(Xe(e)),1),m(g(ue),{value:e.status,severity:g(ce)(e.status),class:`wa-status`},null,8,[`value`,`severity`])])])],10,ge))),128))])]),d(`section`,we,[M.value?(t(),f(h,{key:0},[d(`header`,Te,[m(g(E),{icon:`pi pi-arrow-left`,text:``,rounded:``,class:`wa-back`,"aria-label":`Back`,onClick:et}),d(`span`,{class:u([`wa-avatar support lg`,{online:g(K).presence.staff_online}])},`S`,2),d(`div`,Ee,[d(`h2`,De,r(M.value.subject),1),d(`p`,{class:u([`status-line`,{typing:!!g(K).peerTypingText}])},[g(K).presence.staff_online&&!g(K).peerTypingText?(t(),f(`span`,Oe)):b(``,!0),_(` `+r(Je.value),1)],2)]),d(`span`,{class:u([`live-pill`,{on:g(K).connected}])},r(Ye.value),3)]),d(`div`,{ref_key:`messagesEl`,ref:W,class:u([`wa-messages`,{loading:P.value}])},[d(`div`,ke,`Conversation started · `+r(Y(M.value.created_at)),1),(t(!0),f(h,null,s(N.value,e=>(t(),f(`div`,{key:e.id,class:u([`wa-bubble-row`,{mine:!e.is_staff_reply,theirs:e.is_staff_reply,failed:e._failed}])},[d(`div`,Ae,[e.is_staff_reply?(t(),f(`div`,je,`Support`)):b(``,!0),d(`div`,{class:`wa-text`,innerHTML:g(fe)(e.body)},null,8,Me),d(`div`,Ne,[d(`span`,null,r(X(e.created_at)),1),e.is_staff_reply?b(``,!0):(t(),f(`span`,{key:0,class:u([`ticks`,g(k)(e)]),title:Qe(e)},[g(k)(e)===`pending`?(t(),f(`i`,Fe)):g(k)(e)===`sent`?(t(),f(`i`,Ie)):(t(),f(h,{key:2},[n[14]||=d(`i`,{class:`pi pi-check`},null,-1),n[15]||=d(`i`,{class:`pi pi-check second`},null,-1)],64))],10,Pe)),e._failed?(t(),f(`span`,Le,`Failed`)):b(``,!0)])])],2))),128)),g(K).peerTypingText?(t(),f(`div`,Re,[...n[16]||=[d(`div`,{class:`wa-bubble typing-bubble`},[d(`span`,{class:`dot`}),d(`span`,{class:`dot`}),d(`span`,{class:`dot`})],-1)]])):b(``,!0),!N.value.length&&!P.value?(t(),f(`div`,ze,` Send a message to start the conversation. `)):b(``,!0)],2),J.value?(t(),f(`footer`,Be,[l(d(`textarea`,{"onUpdate:modelValue":n[3]||=e=>F.value=e,rows:`1`,placeholder:`Type a message`,onKeydown:nt,onInput:rt},null,544),[[C,F.value]]),m(g(E),{icon:`pi pi-send`,rounded:``,severity:`success`,loading:L.value,disabled:!F.value.trim(),"aria-label":`Send`,onClick:$},null,8,[`loading`,`disabled`])])):(t(),f(`footer`,Ve,[n[17]||=d(`span`,{class:`muted`},`This conversation is closed. Open a new chat if you need more help.`,-1),m(g(E),{label:`New chat`,icon:`pi pi-plus`,size:`small`,onClick:n[4]||=e=>R.value=!0})]))],64)):(t(),f(`div`,He,[d(`div`,Ue,[n[18]||=d(`div`,{class:`wa-placeholder-icon`},[d(`i`,{class:`pi pi-comments`})],-1),n[19]||=d(`h2`,null,`CryptoInvest Support`,-1),n[20]||=d(`p`,{class:`muted`},` Realtime chat with typing indicators and read receipts — just like WhatsApp. `,-1),m(g(E),{label:`New conversation`,icon:`pi pi-plus`,onClick:n[5]||=e=>R.value=!0}),g(S).displayName?(t(),f(`p`,We,`Signed in as `+r(g(S).displayName),1)):b(``,!0)])]))]),m(g(w),{visible:R.value,"onUpdate:visible":n[9]||=e=>R.value=e,modal:``,header:`New conversation`,class:`w-dialog`},{default:te(()=>[d(`div`,Ge,[d(`label`,null,[n[21]||=_(`Category `,-1),m(g(se),{modelValue:G.value.category,"onUpdate:modelValue":n[6]||=e=>G.value.category=e,options:Ke,"option-label":`label`,"option-value":`value`,class:`w-full`},null,8,[`modelValue`])]),d(`label`,null,[n[22]||=_(`Subject `,-1),m(g(O),{modelValue:G.value.subject,"onUpdate:modelValue":n[7]||=e=>G.value.subject=e,class:`w-full`,placeholder:`Brief summary`},null,8,[`modelValue`])]),d(`label`,null,[n[23]||=_(`Message `,-1),m(g(I),{modelValue:G.value.body,"onUpdate:modelValue":n[8]||=e=>G.value.body=e,rows:`5`,class:`w-full`,placeholder:`Describe your issue…`},null,8,[`modelValue`])]),m(g(E),{label:`Start chat`,icon:`pi pi-send`,loading:H.value,onClick:tt},null,8,[`loading`])])]),_:1},8,[`visible`])],2)}}}),[[`__scopeId`,`data-v-5088f00c`]]);export{H as default};