import{$ as e,A as t,C as n,Ct as r,E as i,F as a,H as o,M as s,O as ee,S as c,U as te,W as l,bt as u,c as d,d as f,g as p,h as m,i as h,it as g,m as _,s as v,t as y,u as b}from"./_plugin-vue_export-helper-BnoIuITy.js";import{Z as x,r as S}from"./basecomponent-Dbv6nt4q.js";import{E as C,a as ne,h as re,i as ie,m as ae,n as oe,p as se,r as w,s as T}from"./index-2ivYmijo.js";import{t as ce}from"./select-b0-9hP3Y.js";import{n as E,t as D}from"./inputtext-CDm6U5-K.js";import{i as le,r as ue}from"./money-D_sYmORa.js";import{t as de}from"./tag-CRT_n1fE.js";import{n as fe,t as O}from"./useSupportChat-D3B3zzvn.js";var k=S.extend({name:`textarea`,style:`
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
`,classes:{root:function(e){var t=e.instance,n=e.props;return[`p-textarea p-component`,{"p-filled":t.$filled,"p-textarea-resizable ":n.autoResize,"p-textarea-sm p-inputfield-sm":n.size===`small`,"p-textarea-lg p-inputfield-lg":n.size===`large`,"p-invalid":t.$invalid,"p-variant-filled":t.$variant===`filled`,"p-textarea-fluid":t.$fluid}]}}}),A={name:`BaseTextarea`,extends:E,props:{autoResize:Boolean},style:k,provide:function(){return{$pcTextarea:this,$parentInstance:this}}};function j(e){"@babel/helpers - typeof";return j=typeof Symbol==`function`&&typeof Symbol.iterator==`symbol`?function(e){return typeof e}:function(e){return e&&typeof Symbol==`function`&&e.constructor===Symbol&&e!==Symbol.prototype?`symbol`:typeof e},j(e)}function M(e,t,n){return(t=N(t))in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function N(e){var t=P(e,`string`);return j(t)==`symbol`?t:t+``}function P(e,t){if(j(e)!=`object`||!e)return e;var n=e[Symbol.toPrimitive];if(n!==void 0){var r=n.call(e,t);if(j(r)!=`object`)return r;throw TypeError(`@@toPrimitive must return a primitive value.`)}return(t===`string`?String:Number)(e)}var F={name:`Textarea`,extends:A,inheritAttrs:!1,observer:null,mounted:function(){var e=this;this.autoResize&&(this.observer=new ResizeObserver(function(){requestAnimationFrame(function(){e.resize()})}),this.observer.observe(this.$el))},updated:function(){this.autoResize&&this.resize()},beforeUnmount:function(){this.observer&&this.observer.disconnect()},methods:{resize:function(){if(this.$el.offsetParent){var e=this.$el.style.height,t=parseInt(e)||0,n=this.$el.scrollHeight;t&&n<t?(this.$el.style.height=`auto`,this.$el.style.height=`${this.$el.scrollHeight}px`):(!t||n>t)&&(this.$el.style.height=`${n}px`)}},onInput:function(e){this.autoResize&&this.resize(),this.writeValue(e.target.value,e)}},computed:{attrs:function(){return c(this.ptmi(`root`,{context:{filled:this.$filled,disabled:this.disabled}}),this.formField)},dataP:function(){return x(M({invalid:this.$invalid,fluid:this.$fluid,filled:this.$variant===`filled`},this.size,this.size))}}},I=[`value`,`name`,`disabled`,`aria-invalid`,`data-p`];function L(e,n,r,i,a,o){return t(),f(`textarea`,c({class:e.cx(`root`),value:e.d_value,name:e.name,disabled:e.disabled,"aria-invalid":e.invalid||void 0,"data-p":o.dataP,onInput:n[0]||=function(){return o.onInput&&o.onInput.apply(o,arguments)}},o.attrs),null,16,I)}F.render=L;var R={class:`wa-sidebar`},z={class:`wa-side-head`},B={class:`wa-search`},V={class:`wa-chat-list`},pe={key:0,class:`wa-empty-side muted`},me={key:1,class:`wa-empty-side`},he=[`onClick`],ge={class:`wa-avatar support`},_e={class:`wa-row-body`},ve={class:`wa-row-top`},ye={class:`truncate`},be={class:`wa-time`},xe={class:`wa-row-bot`},Se={class:`wa-preview truncate`},Ce={class:`wa-pane`},we={class:`wa-chat-head`},Te={class:`wa-chat-meta`},Ee={class:`truncate`},De={key:0,class:`dot-online`},Oe={class:`wa-day-pill`},ke={class:`wa-bubble`},Ae={key:0,class:`wa-sender`},je={class:`wa-text`},Me={class:`wa-meta`},Ne=[`title`],Pe={key:0,class:`pi pi-clock`},Fe={key:1,class:`pi pi-check`},Ie={key:1,class:`fail-hint`},Le={key:0,class:`wa-bubble-row theirs typing-row`},Re={key:1,class:`wa-empty-msgs muted`},ze={key:0,class:`wa-composer`},Be={key:1,class:`wa-composer closed`},Ve={key:1,class:`wa-placeholder`},He={class:`wa-placeholder-card`},Ue={key:0,class:`wa-you muted`},We={class:`form`},H=y(p({__name:`SupportView`,setup(c){let p=ae(),y=re(),x=se(),S=oe(),E=e(!0),k=e([]),A=e(null),j=e(null),M=e([]),N=e(!1),P=e(``),I=e(!1),L=e(!1),H=e(!1),U=e(``),W=e(null),G=e({subject:``,body:``,category:`general`}),K=fe({isStaff:!1,onMessage:async()=>{await Z()}}),Ge=[{label:`General`,value:`general`},{label:`Deposit`,value:`deposit`},{label:`Withdrawal`,value:`withdrawal`},{label:`Investment`,value:`investment`},{label:`Account`,value:`account`},{label:`KYC`,value:`kyc`},{label:`Technical`,value:`technical`}],q=v(()=>{let e=U.value.trim().toLowerCase();return e?k.value.filter(t=>t.subject.toLowerCase().includes(e)||t.category.toLowerCase().includes(e)||t.status.toLowerCase().includes(e)):k.value}),J=v(()=>{let e=(j.value?.status||``).toLowerCase();return!!j.value&&![`closed`,`resolved`].includes(e)}),Ke=v(()=>K.peerTypingText.value?K.peerTypingText.value:K.presence.value.staff_online?`online`:K.presence.value.staff_last_seen?`last seen ${X(K.presence.value.staff_last_seen)}`:j.value?`${j.value.category} · support chat`:``),qe=v(()=>K.connected.value?K.mode.value===`ws`?`Live`:`Live · sync`:`Connecting…`);function Je(e){let t=e.messages||[];if(!t.length)return`No messages yet`;let n=t[t.length-1],r=n.is_staff_reply?`Support`:`You`,i=(n.body||``).replace(/\s+/g,` `).trim();return`${r}: ${i.slice(0,72)}${i.length>72?`…`:``}`}function Y(e){let t=e.trim().split(/\s+/).filter(Boolean);return t.length?t.length===1?t[0].slice(0,2).toUpperCase():(t[0][0]+t[1][0]).toUpperCase():`S`}function X(e){if(!e)return``;try{let t=new Date(e),n=new Date;return t.getFullYear()===n.getFullYear()&&t.getMonth()===n.getMonth()&&t.getDate()===n.getDate()?t.toLocaleTimeString(void 0,{hour:`2-digit`,minute:`2-digit`}):t.toLocaleDateString(void 0,{month:`short`,day:`numeric`})}catch{return ue(e)}}function Ye(e){if(!e)return``;try{return new Date(e).toLocaleTimeString(void 0,{hour:`2-digit`,minute:`2-digit`})}catch{return``}}function Xe(e){let t=O(e);return t===`pending`?`Sending…`:t===`read`?`Read`:t===`delivered`?`Delivered`:`Sent`}async function Z(e=!1){await n();let t=W.value;if(!t)return;let r=t.scrollHeight-t.scrollTop-t.clientHeight<120;(e||r)&&(t.scrollTop=t.scrollHeight)}async function Ze(){E.value=!0;try{let{data:e}=await w.tickets();k.value=ie(e)}finally{E.value=!1}}async function Q(e,t=!1){if(e){A.value=e,t?y.replace(`/support/${e}`):p.params.id!==e&&y.push(`/support/${e}`),N.value=!0;try{let{data:t}=await w.ticket(e);j.value=t,M.value=[...t.messages||[]];let n=k.value.findIndex(t=>t.id===e);n>=0?k.value[n]={...k.value[n],...t}:k.value=[t,...k.value],K.join(e,M),K.markRead(),await Z(!0)}catch{x.toast(`Not found`,`Conversation not found`,`error`),j.value=null,A.value=null,K.leave(),y.replace(`/support`)}finally{N.value=!1}}}function Qe(){K.leave(),A.value=null,j.value=null,M.value=[],y.push(`/support`)}async function $(){if(!P.value.trim()||!j.value||!J.value||I.value)return;let e=P.value.trim();P.value=``,K.sendTyping(!1),I.value=!0;let t=`tmp-${Date.now()}`,n={id:t,body:e,is_staff_reply:!1,created_at:new Date().toISOString(),sender:S.user?.id||0,sender_name:S.displayName,receipt_status:`pending`,_pending:!0};M.value.push(n),await Z(!0);try{let{data:n}=await w.replyTicket(j.value.id,e),r=n,i=M.value.findIndex(e=>e.id===t);i>=0?M.value[i]={...r,_pending:!1}:K.mergeMessage(r),j.value.updated_at=r.created_at||new Date().toISOString();let a=k.value.findIndex(e=>e.id===j.value.id);a>=0&&(k.value[a]={...k.value[a],messages:M.value,updated_at:j.value.updated_at}),await Z(!0)}catch(e){let n=M.value.findIndex(e=>e.id===t);n>=0&&(M.value[n]={...M.value[n],_pending:!1,_failed:!0}),x.toast(`Failed`,e?.response?.data?.detail||`Could not send`,`error`)}finally{I.value=!1}}async function $e(){if(!G.value.subject.trim()||!G.value.body.trim()){x.toast(`Required`,`Subject and message are required`,`warn`);return}H.value=!0;try{let{data:e}=await w.createTicket(G.value);x.toast(`Started`,`Conversation opened with support`,`success`),L.value=!1,G.value={subject:``,body:``,category:`general`},k.value=[e,...k.value.filter(t=>t.id!==e.id)],await Q(e.id,!0)}catch(e){x.toast(`Failed`,e?.response?.data?.detail||`Could not create ticket`,`error`)}finally{H.value=!1}}function et(e){e.key===`Enter`&&!e.shiftKey&&(e.preventDefault(),$())}function tt(){K.onComposerInput()}return o(()=>p.params.id,e=>{typeof e==`string`&&e?A.value!==e&&Q(e,!0):(K.leave(),A.value=null,j.value=null,M.value=[])}),i(async()=>{await Ze();let e=p.params.id;typeof e==`string`&&e&&await Q(e,!0)}),ee(()=>K.leave()),(e,n)=>{let i=a(`tooltip`);return t(),f(`div`,{class:u([`wa-shell`,{"has-chat":!!A.value}])},[d(`aside`,R,[d(`header`,z,[n[10]||=d(`div`,{class:`wa-side-title`},[d(`span`,{class:`wa-brand-dot`}),d(`div`,null,[d(`h1`,null,`Support`),d(`p`,{class:`muted`},`Realtime chat`)])],-1),l(m(g(T),{icon:`pi pi-plus`,rounded:``,severity:`success`,"aria-label":`New chat`,onClick:n[0]||=e=>L.value=!0},null,512),[[i,`New chat`,void 0,{bottom:!0}]])]),d(`div`,B,[n[11]||=d(`i`,{class:`pi pi-search`},null,-1),l(d(`input`,{"onUpdate:modelValue":n[1]||=e=>U.value=e,type:`search`,placeholder:`Search chats`},null,512),[[C,U.value]])]),d(`div`,V,[E.value?(t(),f(`div`,pe,`Loading chats…`)):q.value.length?b(``,!0):(t(),f(`div`,me,[n[12]||=d(`i`,{class:`pi pi-comments`},null,-1),n[13]||=d(`p`,null,`No conversations yet`,-1),m(g(T),{label:`Start a chat`,icon:`pi pi-plus`,size:`small`,onClick:n[2]||=e=>L.value=!0})])),(t(!0),f(h,null,s(q.value,e=>(t(),f(`button`,{key:e.id,type:`button`,class:u([`wa-chat-row`,{active:A.value===e.id}]),onClick:t=>Q(e.id)},[d(`span`,ge,r(Y(e.subject)),1),d(`span`,_e,[d(`span`,ve,[d(`strong`,ye,r(e.subject),1),d(`span`,be,r(X(e.updated_at)),1)]),d(`span`,xe,[d(`span`,Se,r(Je(e)),1),m(g(de),{value:e.status,severity:g(le)(e.status),class:`wa-status`},null,8,[`value`,`severity`])])])],10,he))),128))])]),d(`section`,Ce,[j.value?(t(),f(h,{key:0},[d(`header`,we,[m(g(T),{icon:`pi pi-arrow-left`,text:``,rounded:``,class:`wa-back`,"aria-label":`Back`,onClick:Qe}),d(`span`,{class:u([`wa-avatar support lg`,{online:g(K).presence.staff_online}])},`S`,2),d(`div`,Te,[d(`h2`,Ee,r(j.value.subject),1),d(`p`,{class:u([`status-line`,{typing:!!g(K).peerTypingText}])},[g(K).presence.staff_online&&!g(K).peerTypingText?(t(),f(`span`,De)):b(``,!0),_(` `+r(Ke.value),1)],2)]),d(`span`,{class:u([`live-pill`,{on:g(K).connected}])},r(qe.value),3)]),d(`div`,{ref_key:`messagesEl`,ref:W,class:u([`wa-messages`,{loading:N.value}])},[d(`div`,Oe,`Conversation started · `+r(X(j.value.created_at)),1),(t(!0),f(h,null,s(M.value,e=>(t(),f(`div`,{key:e.id,class:u([`wa-bubble-row`,{mine:!e.is_staff_reply,theirs:e.is_staff_reply,failed:e._failed}])},[d(`div`,ke,[e.is_staff_reply?(t(),f(`div`,Ae,`Support`)):b(``,!0),d(`div`,je,r(e.body),1),d(`div`,Me,[d(`span`,null,r(Ye(e.created_at)),1),e.is_staff_reply?b(``,!0):(t(),f(`span`,{key:0,class:u([`ticks`,g(O)(e)]),title:Xe(e)},[g(O)(e)===`pending`?(t(),f(`i`,Pe)):g(O)(e)===`sent`?(t(),f(`i`,Fe)):(t(),f(h,{key:2},[n[14]||=d(`i`,{class:`pi pi-check`},null,-1),n[15]||=d(`i`,{class:`pi pi-check second`},null,-1)],64))],10,Ne)),e._failed?(t(),f(`span`,Ie,`Failed`)):b(``,!0)])])],2))),128)),g(K).peerTypingText?(t(),f(`div`,Le,[...n[16]||=[d(`div`,{class:`wa-bubble typing-bubble`},[d(`span`,{class:`dot`}),d(`span`,{class:`dot`}),d(`span`,{class:`dot`})],-1)]])):b(``,!0),!M.value.length&&!N.value?(t(),f(`div`,Re,` Send a message to start the conversation. `)):b(``,!0)],2),J.value?(t(),f(`footer`,ze,[l(d(`textarea`,{"onUpdate:modelValue":n[3]||=e=>P.value=e,rows:`1`,placeholder:`Type a message`,onKeydown:et,onInput:tt},null,544),[[C,P.value]]),m(g(T),{icon:`pi pi-send`,rounded:``,severity:`success`,loading:I.value,disabled:!P.value.trim(),"aria-label":`Send`,onClick:$},null,8,[`loading`,`disabled`])])):(t(),f(`footer`,Be,[n[17]||=d(`span`,{class:`muted`},`This conversation is closed. Open a new chat if you need more help.`,-1),m(g(T),{label:`New chat`,icon:`pi pi-plus`,size:`small`,onClick:n[4]||=e=>L.value=!0})]))],64)):(t(),f(`div`,Ve,[d(`div`,He,[n[18]||=d(`div`,{class:`wa-placeholder-icon`},[d(`i`,{class:`pi pi-comments`})],-1),n[19]||=d(`h2`,null,`CryptoInvest Support`,-1),n[20]||=d(`p`,{class:`muted`},` Realtime chat with typing indicators and read receipts — just like WhatsApp. `,-1),m(g(T),{label:`New conversation`,icon:`pi pi-plus`,onClick:n[5]||=e=>L.value=!0}),g(S).displayName?(t(),f(`p`,Ue,`Signed in as `+r(g(S).displayName),1)):b(``,!0)])]))]),m(g(ne),{visible:L.value,"onUpdate:visible":n[9]||=e=>L.value=e,modal:``,header:`New conversation`,class:`w-dialog`},{default:te(()=>[d(`div`,We,[d(`label`,null,[n[21]||=_(`Category `,-1),m(g(ce),{modelValue:G.value.category,"onUpdate:modelValue":n[6]||=e=>G.value.category=e,options:Ge,"option-label":`label`,"option-value":`value`,class:`w-full`},null,8,[`modelValue`])]),d(`label`,null,[n[22]||=_(`Subject `,-1),m(g(D),{modelValue:G.value.subject,"onUpdate:modelValue":n[7]||=e=>G.value.subject=e,class:`w-full`,placeholder:`Brief summary`},null,8,[`modelValue`])]),d(`label`,null,[n[23]||=_(`Message `,-1),m(g(F),{modelValue:G.value.body,"onUpdate:modelValue":n[8]||=e=>G.value.body=e,rows:`5`,class:`w-full`,placeholder:`Describe your issue…`},null,8,[`modelValue`])]),m(g(T),{label:`Start chat`,icon:`pi pi-send`,loading:H.value,onClick:$e},null,8,[`loading`])])]),_:1},8,[`visible`])],2)}}}),[[`__scopeId`,`data-v-098eecf2`]]);export{H as default};