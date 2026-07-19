import{$ as e,A as t,E as n,N as r,S as i,c as a,d as o,g as s,h as c,it as l,l as u,m as d,s as f,t as p,u as m,xt as h}from"./_plugin-vue_export-helper-BJ6WweKP.js";import{Z as g,r as _}from"./basecomponent-BTtfM7n9.js";import{h as v,n as y,p as b,r as x,s as S,t as C}from"./index-Djmxx1do.js";import{t as w}from"./select-BUdHqezM.js";import{n as T}from"./baseinput-Bapp2sLS.js";import{t as E}from"./inputtext-CWKqdetO.js";import{n as D}from"./money-D_sYmORa.js";import{t as O}from"./PageHeader-rxFhlkHw.js";import{t as k}from"./tag-BENBlpQk.js";var A=_.extend({name:`toggleswitch`,style:`
    .p-toggleswitch {
        display: inline-block;
        width: dt('toggleswitch.width');
        height: dt('toggleswitch.height');
    }

    .p-toggleswitch-input {
        cursor: pointer;
        appearance: none;
        position: absolute;
        top: 0;
        inset-inline-start: 0;
        width: 100%;
        height: 100%;
        padding: 0;
        margin: 0;
        opacity: 0;
        z-index: 1;
        outline: 0 none;
        border-radius: dt('toggleswitch.border.radius');
    }

    .p-toggleswitch-slider {
        cursor: pointer;
        width: 100%;
        height: 100%;
        border-width: dt('toggleswitch.border.width');
        border-style: solid;
        border-color: dt('toggleswitch.border.color');
        background: dt('toggleswitch.background');
        transition:
            background dt('toggleswitch.transition.duration'),
            color dt('toggleswitch.transition.duration'),
            border-color dt('toggleswitch.transition.duration'),
            outline-color dt('toggleswitch.transition.duration'),
            box-shadow dt('toggleswitch.transition.duration');
        border-radius: dt('toggleswitch.border.radius');
        outline-color: transparent;
        box-shadow: dt('toggleswitch.shadow');
    }

    .p-toggleswitch-handle {
        position: absolute;
        top: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        background: dt('toggleswitch.handle.background');
        color: dt('toggleswitch.handle.color');
        width: dt('toggleswitch.handle.size');
        height: dt('toggleswitch.handle.size');
        inset-inline-start: dt('toggleswitch.gap');
        margin-block-start: calc(-1 * calc(dt('toggleswitch.handle.size') / 2));
        border-radius: dt('toggleswitch.handle.border.radius');
        transition:
            background dt('toggleswitch.transition.duration'),
            color dt('toggleswitch.transition.duration'),
            inset-inline-start dt('toggleswitch.slide.duration'),
            box-shadow dt('toggleswitch.slide.duration');
    }

    .p-toggleswitch.p-toggleswitch-checked .p-toggleswitch-slider {
        background: dt('toggleswitch.checked.background');
        border-color: dt('toggleswitch.checked.border.color');
    }

    .p-toggleswitch.p-toggleswitch-checked .p-toggleswitch-handle {
        background: dt('toggleswitch.handle.checked.background');
        color: dt('toggleswitch.handle.checked.color');
        inset-inline-start: calc(dt('toggleswitch.width') - calc(dt('toggleswitch.handle.size') + dt('toggleswitch.gap')));
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:hover) .p-toggleswitch-slider {
        background: dt('toggleswitch.hover.background');
        border-color: dt('toggleswitch.hover.border.color');
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:hover) .p-toggleswitch-handle {
        background: dt('toggleswitch.handle.hover.background');
        color: dt('toggleswitch.handle.hover.color');
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:hover).p-toggleswitch-checked .p-toggleswitch-slider {
        background: dt('toggleswitch.checked.hover.background');
        border-color: dt('toggleswitch.checked.hover.border.color');
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:hover).p-toggleswitch-checked .p-toggleswitch-handle {
        background: dt('toggleswitch.handle.checked.hover.background');
        color: dt('toggleswitch.handle.checked.hover.color');
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:focus-visible) .p-toggleswitch-slider {
        box-shadow: dt('toggleswitch.focus.ring.shadow');
        outline: dt('toggleswitch.focus.ring.width') dt('toggleswitch.focus.ring.style') dt('toggleswitch.focus.ring.color');
        outline-offset: dt('toggleswitch.focus.ring.offset');
    }

    .p-toggleswitch.p-invalid > .p-toggleswitch-slider {
        border-color: dt('toggleswitch.invalid.border.color');
    }

    .p-toggleswitch.p-disabled {
        opacity: 1;
    }

    .p-toggleswitch.p-disabled .p-toggleswitch-slider {
        background: dt('toggleswitch.disabled.background');
    }

    .p-toggleswitch.p-disabled .p-toggleswitch-handle {
        background: dt('toggleswitch.handle.disabled.background');
    }
`,classes:{root:function(e){var t=e.instance,n=e.props;return[`p-toggleswitch p-component`,{"p-toggleswitch-checked":t.checked,"p-disabled":n.disabled,"p-invalid":t.$invalid}]},input:`p-toggleswitch-input`,slider:`p-toggleswitch-slider`,handle:`p-toggleswitch-handle`},inlineStyles:{root:{position:`relative`}}}),j={name:`ToggleSwitch`,extends:{name:`BaseToggleSwitch`,extends:T,props:{trueValue:{type:null,default:!0},falseValue:{type:null,default:!1},readonly:{type:Boolean,default:!1},tabindex:{type:Number,default:null},inputId:{type:String,default:null},inputClass:{type:[String,Object],default:null},inputStyle:{type:Object,default:null},ariaLabelledby:{type:String,default:null},ariaLabel:{type:String,default:null}},style:A,provide:function(){return{$pcToggleSwitch:this,$parentInstance:this}}},inheritAttrs:!1,emits:[`change`,`focus`,`blur`],methods:{getPTOptions:function(e){return(e===`root`?this.ptmi:this.ptm)(e,{context:{checked:this.checked,disabled:this.disabled}})},onChange:function(e){if(!this.disabled&&!this.readonly){var t=this.checked?this.falseValue:this.trueValue;this.writeValue(t,e),this.$emit(`change`,e)}},onFocus:function(e){this.$emit(`focus`,e)},onBlur:function(e){var t,n;this.$emit(`blur`,e),(t=(n=this.formField).onBlur)==null||t.call(n,e)}},computed:{checked:function(){return this.d_value===this.trueValue},dataP:function(){return g({checked:this.checked,disabled:this.disabled,invalid:this.$invalid})}}},M=[`data-p-checked`,`data-p-disabled`,`data-p`],N=[`id`,`checked`,`tabindex`,`disabled`,`readonly`,`aria-checked`,`aria-labelledby`,`aria-label`,`aria-invalid`],P=[`data-p`],F=[`data-p`];function I(e,n,s,c,l,u){return t(),o(`div`,i({class:e.cx(`root`),style:e.sx(`root`)},u.getPTOptions(`root`),{"data-p-checked":u.checked,"data-p-disabled":e.disabled,"data-p":u.dataP}),[a(`input`,i({id:e.inputId,type:`checkbox`,role:`switch`,class:[e.cx(`input`),e.inputClass],style:e.inputStyle,checked:u.checked,tabindex:e.tabindex,disabled:e.disabled,readonly:e.readonly,"aria-checked":u.checked,"aria-labelledby":e.ariaLabelledby,"aria-label":e.ariaLabel,"aria-invalid":e.invalid||void 0,onFocus:n[0]||=function(){return u.onFocus&&u.onFocus.apply(u,arguments)},onBlur:n[1]||=function(){return u.onBlur&&u.onBlur.apply(u,arguments)},onChange:n[2]||=function(){return u.onChange&&u.onChange.apply(u,arguments)}},u.getPTOptions(`input`)),null,16,N),a(`div`,i({class:e.cx(`slider`)},u.getPTOptions(`slider`),{"data-p":u.dataP}),[a(`div`,i({class:e.cx(`handle`)},u.getPTOptions(`handle`),{"data-p":u.dataP}),[r(e.$slots,`handle`,{checked:u.checked})],16,F)],16,P)],16,M)}j.render=I;var L={class:`grid`},R={class:`glass card`},z={class:`avatar`},B={class:`muted`},V={class:`tags`},H={class:`mono`},U={class:`mono success`},W={class:`actions`},G={class:`stack`},K={class:`glass card`},q={class:`form`},J={class:`switch-row`},Y={class:`switch-row`},X={class:`glass card`},Z={class:`field`},Q=[`data-theme-preview`],$=p(s({__name:`ProfileView`,setup(r){let i=y(),s=C(),p=b(),g=v(),_=e(!1),T=e({first_name:``,last_name:``,phone:``,country:``,preferred_currency:``,email_alerts:!0,sms_alerts:!1}),A=[{label:`Dark (Premium)`,value:`dark`},{label:`Light`,value:`light`},{label:`Glass`,value:`glass`},{label:`Classic`,value:`classic`}],M=f({get:()=>s.mode,set:e=>s.apply(e)});n(()=>{let e=i.user;e&&(T.value={first_name:e.first_name||``,last_name:e.last_name||``,phone:e.phone||``,country:e.country||``,preferred_currency:e.preferred_currency||``,email_alerts:e.email_alerts!==!1,sms_alerts:!!e.sms_alerts})});async function N(){_.value=!0;try{await x.updateProfile(T.value),await i.fetchMe(),p.toast(`Saved`,`Profile updated`,`success`)}catch(e){p.toast(`Failed`,e?.response?.data?.detail||`Could not save`,`error`)}finally{_.value=!1}}return(e,n)=>(t(),o(`div`,null,[c(O,{title:`Profile`,subtitle:`Account, preferences, and security`}),a(`div`,L,[a(`div`,R,[a(`div`,z,h((l(i).displayName||`U`).slice(0,1).toUpperCase()),1),a(`h2`,null,h(l(i).displayName),1),a(`p`,B,h(l(i).user?.email),1),a(`div`,V,[l(i).user?.email_verified?(t(),u(l(k),{key:0,value:`Email verified`,severity:`success`})):(t(),u(l(k),{key:1,value:`Email pending`,severity:`warn`})),l(i).user?.is_kyc_verified?(t(),u(l(k),{key:2,value:`KYC verified`,severity:`success`})):(t(),u(l(k),{key:3,value:`KYC incomplete`,severity:`info`})),l(i).user?.two_factor_enabled?(t(),u(l(k),{key:4,value:`2FA on`,severity:`info`})):m(``,!0)]),a(`ul`,null,[a(`li`,null,[n[12]||=a(`span`,null,`Referral code`,-1),a(`strong`,H,h(l(i).user?.referral_code||`—`),1)]),a(`li`,null,[n[13]||=a(`span`,null,`Referral earnings`,-1),a(`strong`,U,`+`+h(l(D)(l(i).user?.referral_earnings??0)),1)]),a(`li`,null,[n[14]||=a(`span`,null,`Risk score`,-1),a(`strong`,null,h(l(i).user?.risk_score??0),1)])]),a(`div`,W,[c(l(S),{label:`KYC`,icon:`pi pi-id-card`,outlined:``,class:`w-full`,onClick:n[0]||=e=>l(g).push(`/kyc`)}),c(l(S),{label:`Security`,icon:`pi pi-shield`,outlined:``,class:`w-full`,onClick:n[1]||=e=>l(g).push(`/security`)}),c(l(S),{label:`VIP`,icon:`pi pi-crown`,outlined:``,class:`w-full`,onClick:n[2]||=e=>l(g).push(`/vip`)}),c(l(S),{label:`Log out`,icon:`pi pi-sign-out`,severity:`danger`,text:``,class:`w-full`,onClick:n[3]||=e=>l(i).logout()})])]),a(`div`,G,[a(`div`,K,[n[22]||=a(`h3`,null,`Edit profile`,-1),a(`div`,q,[a(`label`,null,[n[15]||=d(`First name `,-1),c(l(E),{modelValue:T.value.first_name,"onUpdate:modelValue":n[4]||=e=>T.value.first_name=e,class:`w-full`},null,8,[`modelValue`])]),a(`label`,null,[n[16]||=d(`Last name `,-1),c(l(E),{modelValue:T.value.last_name,"onUpdate:modelValue":n[5]||=e=>T.value.last_name=e,class:`w-full`},null,8,[`modelValue`])]),a(`label`,null,[n[17]||=d(`Phone `,-1),c(l(E),{modelValue:T.value.phone,"onUpdate:modelValue":n[6]||=e=>T.value.phone=e,class:`w-full`},null,8,[`modelValue`])]),a(`label`,null,[n[18]||=d(`Country `,-1),c(l(E),{modelValue:T.value.country,"onUpdate:modelValue":n[7]||=e=>T.value.country=e,class:`w-full`},null,8,[`modelValue`])]),a(`label`,null,[n[19]||=d(`Display currency `,-1),c(l(E),{modelValue:T.value.preferred_currency,"onUpdate:modelValue":n[8]||=e=>T.value.preferred_currency=e,class:`w-full`,placeholder:`e.g. USDT`},null,8,[`modelValue`])]),a(`div`,J,[n[20]||=a(`span`,null,`Email alerts`,-1),c(l(j),{modelValue:T.value.email_alerts,"onUpdate:modelValue":n[9]||=e=>T.value.email_alerts=e},null,8,[`modelValue`])]),a(`div`,Y,[n[21]||=a(`span`,null,`SMS alerts`,-1),c(l(j),{modelValue:T.value.sms_alerts,"onUpdate:modelValue":n[10]||=e=>T.value.sms_alerts=e},null,8,[`modelValue`])]),c(l(S),{label:`Save profile`,icon:`pi pi-check`,loading:_.value,onClick:N},null,8,[`loading`])])]),a(`div`,X,[n[25]||=a(`h3`,null,`Appearance`,-1),a(`label`,Z,[n[23]||=a(`span`,null,`Theme`,-1),c(l(w),{modelValue:M.value,"onUpdate:modelValue":n[11]||=e=>M.value=e,options:A,"option-label":`label`,"option-value":`value`,class:`w-full`},null,8,[`modelValue`])]),a(`div`,{class:`preview`,"data-theme-preview":l(s).mode},[...n[24]||=[a(`div`,{class:`mini`},null,-1),a(`div`,{class:`mini short`},null,-1)]],8,Q)])])])]))}}),[[`__scopeId`,`data-v-510623d2`]]);export{$ as default};