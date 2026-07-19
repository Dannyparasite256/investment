import{$ as e,A as t,Ct as n,E as r,N as i,S as a,c as o,d as s,g as c,h as l,i as u,it as d,l as f,m as p,s as m,t as h,u as g}from"./_plugin-vue_export-helper-BnoIuITy.js";import{Z as _,r as v}from"./basecomponent-Dbv6nt4q.js";import{h as y,n as b,p as x,r as S,s as C,t as w}from"./index-DNHb-6zn.js";import{t as T}from"./select-2k7uBGdc.js";import{r as E,t as D}from"./inputtext-CDm6U5-K.js";import{n as O}from"./money-D_sYmORa.js";import{t as k}from"./PageHeader-CdgLarmb.js";import{t as A}from"./tag-CRT_n1fE.js";var j=v.extend({name:`toggleswitch`,style:`
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
`,classes:{root:function(e){var t=e.instance,n=e.props;return[`p-toggleswitch p-component`,{"p-toggleswitch-checked":t.checked,"p-disabled":n.disabled,"p-invalid":t.$invalid}]},input:`p-toggleswitch-input`,slider:`p-toggleswitch-slider`,handle:`p-toggleswitch-handle`},inlineStyles:{root:{position:`relative`}}}),M={name:`ToggleSwitch`,extends:{name:`BaseToggleSwitch`,extends:E,props:{trueValue:{type:null,default:!0},falseValue:{type:null,default:!1},readonly:{type:Boolean,default:!1},tabindex:{type:Number,default:null},inputId:{type:String,default:null},inputClass:{type:[String,Object],default:null},inputStyle:{type:Object,default:null},ariaLabelledby:{type:String,default:null},ariaLabel:{type:String,default:null}},style:j,provide:function(){return{$pcToggleSwitch:this,$parentInstance:this}}},inheritAttrs:!1,emits:[`change`,`focus`,`blur`],methods:{getPTOptions:function(e){return(e===`root`?this.ptmi:this.ptm)(e,{context:{checked:this.checked,disabled:this.disabled}})},onChange:function(e){if(!this.disabled&&!this.readonly){var t=this.checked?this.falseValue:this.trueValue;this.writeValue(t,e),this.$emit(`change`,e)}},onFocus:function(e){this.$emit(`focus`,e)},onBlur:function(e){var t,n;this.$emit(`blur`,e),(t=(n=this.formField).onBlur)==null||t.call(n,e)}},computed:{checked:function(){return this.d_value===this.trueValue},dataP:function(){return _({checked:this.checked,disabled:this.disabled,invalid:this.$invalid})}}},N=[`data-p-checked`,`data-p-disabled`,`data-p`],P=[`id`,`checked`,`tabindex`,`disabled`,`readonly`,`aria-checked`,`aria-labelledby`,`aria-label`,`aria-invalid`],F=[`data-p`],I=[`data-p`];function L(e,n,r,c,l,u){return t(),s(`div`,a({class:e.cx(`root`),style:e.sx(`root`)},u.getPTOptions(`root`),{"data-p-checked":u.checked,"data-p-disabled":e.disabled,"data-p":u.dataP}),[o(`input`,a({id:e.inputId,type:`checkbox`,role:`switch`,class:[e.cx(`input`),e.inputClass],style:e.inputStyle,checked:u.checked,tabindex:e.tabindex,disabled:e.disabled,readonly:e.readonly,"aria-checked":u.checked,"aria-labelledby":e.ariaLabelledby,"aria-label":e.ariaLabel,"aria-invalid":e.invalid||void 0,onFocus:n[0]||=function(){return u.onFocus&&u.onFocus.apply(u,arguments)},onBlur:n[1]||=function(){return u.onBlur&&u.onBlur.apply(u,arguments)},onChange:n[2]||=function(){return u.onChange&&u.onChange.apply(u,arguments)}},u.getPTOptions(`input`)),null,16,P),o(`div`,a({class:e.cx(`slider`)},u.getPTOptions(`slider`),{"data-p":u.dataP}),[o(`div`,a({class:e.cx(`handle`)},u.getPTOptions(`handle`),{"data-p":u.dataP}),[i(e.$slots,`handle`,{checked:u.checked})],16,I)],16,F)],16,N)}M.render=L;var R={class:`grid`},z={class:`glass card`},B={class:`avatar`},V=[`src`,`alt`],H={class:`muted`},U={class:`tags`},W={class:`mono`},G={class:`mono success`},K={class:`actions`},q={class:`stack`},J={class:`glass card`},Y={class:`form`},X={class:`switch-row`},Z={class:`switch-row`},Q={class:`glass card`},$={class:`field`},ee=[`data-theme-preview`],te=h(c({__name:`ProfileView`,setup(i){let a=b(),c=w(),h=x(),_=y(),v=e(!1),E=e({first_name:``,last_name:``,phone:``,country:``,preferred_currency:``,email_alerts:!0,sms_alerts:!1}),j=[{label:`Dark (Premium)`,value:`dark`},{label:`Light`,value:`light`},{label:`Glass`,value:`glass`},{label:`Classic`,value:`classic`}],N=m({get:()=>c.mode,set:e=>c.apply(e)});r(()=>{let e=a.user;e&&(E.value={first_name:e.first_name||``,last_name:e.last_name||``,phone:e.phone||``,country:e.country||``,preferred_currency:e.preferred_currency||``,email_alerts:e.email_alerts!==!1,sms_alerts:!!e.sms_alerts})});async function P(){v.value=!0;try{await S.updateProfile(E.value),await a.fetchMe(),h.toast(`Saved`,`Profile updated`,`success`)}catch(e){h.toast(`Failed`,e?.response?.data?.detail||`Could not save`,`error`)}finally{v.value=!1}}return(e,r)=>(t(),s(`div`,null,[l(k,{title:`Profile`,subtitle:`Account, preferences, and security`}),o(`div`,R,[o(`div`,z,[o(`div`,B,[d(a).user?.avatar_url?(t(),s(`img`,{key:0,src:d(a).user.avatar_url,alt:d(a).displayName,class:`avatar-img`,referrerpolicy:`no-referrer`},null,8,V)):(t(),s(u,{key:1},[p(n((d(a).displayName||`U`).slice(0,1).toUpperCase()),1)],64))]),o(`h2`,null,n(d(a).displayName),1),o(`p`,H,n(d(a).user?.email),1),o(`div`,U,[d(a).user?.email_verified?(t(),f(d(A),{key:0,value:`Email verified`,severity:`success`})):(t(),f(d(A),{key:1,value:`Email pending`,severity:`warn`})),d(a).user?.is_kyc_verified?(t(),f(d(A),{key:2,value:`KYC verified`,severity:`success`})):(t(),f(d(A),{key:3,value:`KYC incomplete`,severity:`info`})),d(a).user?.two_factor_enabled?(t(),f(d(A),{key:4,value:`2FA on`,severity:`info`})):g(``,!0)]),o(`ul`,null,[o(`li`,null,[r[12]||=o(`span`,null,`Referral code`,-1),o(`strong`,W,n(d(a).user?.referral_code||`—`),1)]),o(`li`,null,[r[13]||=o(`span`,null,`Referral earnings`,-1),o(`strong`,G,`+`+n(d(O)(d(a).user?.referral_earnings??0)),1)]),o(`li`,null,[r[14]||=o(`span`,null,`Risk score`,-1),o(`strong`,null,n(d(a).user?.risk_score??0),1)])]),o(`div`,K,[l(d(C),{label:`KYC`,icon:`pi pi-id-card`,outlined:``,class:`w-full`,onClick:r[0]||=e=>d(_).push(`/kyc`)}),l(d(C),{label:`Security`,icon:`pi pi-shield`,outlined:``,class:`w-full`,onClick:r[1]||=e=>d(_).push(`/security`)}),l(d(C),{label:`VIP`,icon:`pi pi-crown`,outlined:``,class:`w-full`,onClick:r[2]||=e=>d(_).push(`/vip`)}),l(d(C),{label:`Log out`,icon:`pi pi-sign-out`,severity:`danger`,text:``,class:`w-full`,onClick:r[3]||=e=>d(a).logout()})])]),o(`div`,q,[o(`div`,J,[r[22]||=o(`h3`,null,`Edit profile`,-1),o(`div`,Y,[o(`label`,null,[r[15]||=p(`First name `,-1),l(d(D),{modelValue:E.value.first_name,"onUpdate:modelValue":r[4]||=e=>E.value.first_name=e,class:`w-full`},null,8,[`modelValue`])]),o(`label`,null,[r[16]||=p(`Last name `,-1),l(d(D),{modelValue:E.value.last_name,"onUpdate:modelValue":r[5]||=e=>E.value.last_name=e,class:`w-full`},null,8,[`modelValue`])]),o(`label`,null,[r[17]||=p(`Phone `,-1),l(d(D),{modelValue:E.value.phone,"onUpdate:modelValue":r[6]||=e=>E.value.phone=e,class:`w-full`},null,8,[`modelValue`])]),o(`label`,null,[r[18]||=p(`Country `,-1),l(d(D),{modelValue:E.value.country,"onUpdate:modelValue":r[7]||=e=>E.value.country=e,class:`w-full`},null,8,[`modelValue`])]),o(`label`,null,[r[19]||=p(`Display currency `,-1),l(d(D),{modelValue:E.value.preferred_currency,"onUpdate:modelValue":r[8]||=e=>E.value.preferred_currency=e,class:`w-full`,placeholder:`e.g. USDT`},null,8,[`modelValue`])]),o(`div`,X,[r[20]||=o(`span`,null,`Email alerts`,-1),l(d(M),{modelValue:E.value.email_alerts,"onUpdate:modelValue":r[9]||=e=>E.value.email_alerts=e},null,8,[`modelValue`])]),o(`div`,Z,[r[21]||=o(`span`,null,`SMS alerts`,-1),l(d(M),{modelValue:E.value.sms_alerts,"onUpdate:modelValue":r[10]||=e=>E.value.sms_alerts=e},null,8,[`modelValue`])]),l(d(C),{label:`Save profile`,icon:`pi pi-check`,loading:v.value,onClick:P},null,8,[`loading`])])]),o(`div`,Q,[r[25]||=o(`h3`,null,`Appearance`,-1),o(`label`,$,[r[23]||=o(`span`,null,`Theme`,-1),l(d(T),{modelValue:N.value,"onUpdate:modelValue":r[11]||=e=>N.value=e,options:j,"option-label":`label`,"option-value":`value`,class:`w-full`},null,8,[`modelValue`])]),o(`div`,{class:`preview`,"data-theme-preview":d(c).mode},[...r[24]||=[o(`div`,{class:`mini`},null,-1),o(`div`,{class:`mini short`},null,-1)]],8,ee)])])])]))}}),[[`__scopeId`,`data-v-650d68ea`]]);export{te as default};