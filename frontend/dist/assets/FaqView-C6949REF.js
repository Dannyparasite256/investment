import{$ as e,A as t,E as n,F as r,I as i,M as a,N as o,P as s,S as c,U as l,W as u,c as d,d as f,g as p,h as m,i as h,it as g,l as _,m as v,s as y,t as b,u as x,vt as S,xt as C}from"./_plugin-vue_export-helper-BJ6WweKP.js";import{C as w,R as T,X as E,Z as D,r as O,t as k}from"./basecomponent-BTtfM7n9.js";import{n as A,t as ee}from"./ripple-twiqNQSu.js";import{T as te,r as j,w as M}from"./index-Dt333Id3.js";import{t as N}from"./PageHeader-rxFhlkHw.js";import{t as P}from"./EmptyState-Cnz5XLo5.js";import{t as F}from"./chevrondown-Ci9PJp5p.js";import{t as I}from"./chevronright-CcaulikD.js";var L={name:`ChevronUpIcon`,extends:A};function R(e){return H(e)||V(e)||B(e)||z()}function z(){throw TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function B(e,t){if(e){if(typeof e==`string`)return U(e,t);var n={}.toString.call(e).slice(8,-1);return n===`Object`&&e.constructor&&(n=e.constructor.name),n===`Map`||n===`Set`?Array.from(e):n===`Arguments`||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?U(e,t):void 0}}function V(e){if(typeof Symbol<`u`&&e[Symbol.iterator]!=null||e[`@@iterator`]!=null)return Array.from(e)}function H(e){if(Array.isArray(e))return U(e)}function U(e,t){(t==null||t>e.length)&&(t=e.length);for(var n=0,r=Array(t);n<t;n++)r[n]=e[n];return r}function W(e,n,r,i,a,o){return t(),f(`svg`,c({width:`14`,height:`14`,viewBox:`0 0 14 14`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`},e.pti()),R(n[0]||=[d(`path`,{d:`M12.2097 10.4113C12.1057 10.4118 12.0027 10.3915 11.9067 10.3516C11.8107 10.3118 11.7237 10.2532 11.6506 10.1792L6.93602 5.46461L2.22139 10.1476C2.07272 10.244 1.89599 10.2877 1.71953 10.2717C1.54307 10.2556 1.3771 10.1808 1.24822 10.0593C1.11933 9.93766 1.035 9.77633 1.00874 9.6011C0.982477 9.42587 1.0158 9.2469 1.10338 9.09287L6.37701 3.81923C6.52533 3.6711 6.72639 3.58789 6.93602 3.58789C7.14565 3.58789 7.3467 3.6711 7.49502 3.81923L12.7687 9.09287C12.9168 9.24119 13 9.44225 13 9.65187C13 9.8615 12.9168 10.0626 12.7687 10.2109C12.616 10.3487 12.4151 10.4207 12.2097 10.4113Z`,fill:`currentColor`},null,-1)]),16)}L.render=W;var G=O.extend({name:`accordioncontent`,classes:{root:`p-accordioncontent`,contentWrapper:`p-accordioncontent-wrapper`,content:`p-accordioncontent-content`}}),K={name:`AccordionContent`,extends:{name:`BaseAccordionContent`,extends:k,props:{as:{type:[String,Object],default:`DIV`},asChild:{type:Boolean,default:!1}},style:G,provide:function(){return{$pcAccordionContent:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcAccordion`,`$pcAccordionPanel`],computed:{id:function(){return`${this.$pcAccordion.$id}_accordioncontent_${this.$pcAccordionPanel.value}`},ariaLabelledby:function(){return`${this.$pcAccordion.$id}_accordionheader_${this.$pcAccordionPanel.value}`},attrs:function(){return c(this.a11yAttrs,this.ptmi(`root`,this.ptParams))},a11yAttrs:function(){return{id:this.id,role:`region`,"aria-labelledby":this.ariaLabelledby,"data-pc-name":`accordioncontent`,"data-p-active":this.$pcAccordionPanel.active}},ptParams:function(){return{context:{active:this.$pcAccordionPanel.active}}}}};function q(e,n,r,a,s,f){return e.asChild?o(e.$slots,`default`,{key:1,class:S(e.cx(`root`)),active:f.$pcAccordionPanel.active,a11yAttrs:f.a11yAttrs}):(t(),_(M,c({key:0,name:`p-collapsible`},e.ptm(`transition`,f.ptParams)),{default:l(function(){return[!f.$pcAccordion.lazy||f.$pcAccordionPanel.active?u((t(),_(i(e.as),c({key:0,class:e.cx(`root`)},f.attrs),{default:l(function(){return[d(`div`,c({class:e.cx(`contentWrapper`)},e.ptm(`contentWrapper`,f.ptParams)),[d(`div`,c({class:e.cx(`content`)},e.ptm(`content`,f.ptParams)),[o(e.$slots,`default`)],16)],16)]}),_:3},16,[`class`])),[[te,f.$pcAccordion.lazy?!0:f.$pcAccordionPanel.active]]):x(``,!0)]}),_:3},16))}K.render=q;var J=O.extend({name:`accordionheader`,classes:{root:`p-accordionheader`,toggleicon:`p-accordionheader-toggle-icon`}}),Y={name:`AccordionHeader`,extends:{name:`BaseAccordionHeader`,extends:k,props:{as:{type:[String,Object],default:`BUTTON`},asChild:{type:Boolean,default:!1}},style:J,provide:function(){return{$pcAccordionHeader:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcAccordion`,`$pcAccordionPanel`],methods:{onFocus:function(){this.$pcAccordion.selectOnFocus&&this.changeActiveValue()},onClick:function(){!this.$pcAccordion.selectOnFocus&&this.changeActiveValue()},onKeydown:function(e){switch(e.code){case`ArrowDown`:this.onArrowDownKey(e);break;case`ArrowUp`:this.onArrowUpKey(e);break;case`Home`:this.onHomeKey(e);break;case`End`:this.onEndKey(e);break;case`Enter`:case`NumpadEnter`:case`Space`:this.onEnterKey(e);break}},onArrowDownKey:function(e){var t=this.findNextPanel(this.findPanel(e.currentTarget));t?this.changeFocusedPanel(e,t):this.onHomeKey(e),e.preventDefault()},onArrowUpKey:function(e){var t=this.findPrevPanel(this.findPanel(e.currentTarget));t?this.changeFocusedPanel(e,t):this.onEndKey(e),e.preventDefault()},onHomeKey:function(e){var t=this.findFirstPanel();this.changeFocusedPanel(e,t),e.preventDefault()},onEndKey:function(e){var t=this.findLastPanel();this.changeFocusedPanel(e,t),e.preventDefault()},onEnterKey:function(e){this.changeActiveValue(),e.preventDefault()},findPanel:function(e){return e?.closest(`[data-pc-name="accordionpanel"]`)},findHeader:function(e){return E(e,`[data-pc-name="accordionheader"]`)},findNextPanel:function(e){var t=arguments.length>1&&arguments[1]!==void 0&&arguments[1]?e:e.nextElementSibling;return t?w(t,`data-p-disabled`)?this.findNextPanel(t):this.findHeader(t):null},findPrevPanel:function(e){var t=arguments.length>1&&arguments[1]!==void 0&&arguments[1]?e:e.previousElementSibling;return t?w(t,`data-p-disabled`)?this.findPrevPanel(t):this.findHeader(t):null},findFirstPanel:function(){return this.findNextPanel(this.$pcAccordion.$el.firstElementChild,!0)},findLastPanel:function(){return this.findPrevPanel(this.$pcAccordion.$el.lastElementChild,!0)},changeActiveValue:function(){this.$pcAccordion.updateValue(this.$pcAccordionPanel.value)},changeFocusedPanel:function(e,t){T(this.findHeader(t))}},computed:{id:function(){return`${this.$pcAccordion.$id}_accordionheader_${this.$pcAccordionPanel.value}`},ariaControls:function(){return`${this.$pcAccordion.$id}_accordioncontent_${this.$pcAccordionPanel.value}`},attrs:function(){return c(this.asAttrs,this.a11yAttrs,this.ptmi(`root`,this.ptParams))},asAttrs:function(){return this.as===`BUTTON`?{type:`button`,disabled:this.$pcAccordionPanel.disabled}:void 0},a11yAttrs:function(){return{id:this.id,tabindex:this.$pcAccordion.tabindex,"aria-expanded":this.$pcAccordionPanel.active,"aria-controls":this.ariaControls,"data-pc-name":`accordionheader`,"data-p-disabled":this.$pcAccordionPanel.disabled,"data-p-active":this.$pcAccordionPanel.active,onFocus:this.onFocus,onKeydown:this.onKeydown}},ptParams:function(){return{context:{active:this.$pcAccordionPanel.active}}},dataP:function(){return D({active:this.$pcAccordionPanel.active})}},components:{ChevronUpIcon:L,ChevronDownIcon:F},directives:{ripple:ee}};function X(e,n,a,s,d,f){var p=r(`ripple`);return e.asChild?o(e.$slots,`default`,{key:1,class:S(e.cx(`root`)),active:f.$pcAccordionPanel.active,a11yAttrs:f.a11yAttrs,onClick:f.onClick}):u((t(),_(i(e.as),c({key:0,"data-p":f.dataP,class:e.cx(`root`),onClick:f.onClick},f.attrs),{default:l(function(){return[o(e.$slots,`default`,{active:f.$pcAccordionPanel.active}),o(e.$slots,`toggleicon`,{active:f.$pcAccordionPanel.active,class:S(e.cx(`toggleicon`))},function(){return[f.$pcAccordionPanel.active?(t(),_(i(f.$pcAccordion.$slots.collapseicon?f.$pcAccordion.$slots.collapseicon:f.$pcAccordion.collapseIcon?`span`:`ChevronUpIcon`),c({key:0,class:[f.$pcAccordion.collapseIcon,e.cx(`toggleicon`)],"aria-hidden":`true`},e.ptm(`toggleicon`,f.ptParams)),null,16,[`class`])):(t(),_(i(f.$pcAccordion.$slots.expandicon?f.$pcAccordion.$slots.expandicon:f.$pcAccordion.expandIcon?`span`:`ChevronDownIcon`),c({key:1,class:[f.$pcAccordion.expandIcon,e.cx(`toggleicon`)],"aria-hidden":`true`},e.ptm(`toggleicon`,f.ptParams)),null,16,[`class`]))]})]}),_:3},16,[`data-p`,`class`,`onClick`])),[[p]])}Y.render=X;var Z=O.extend({name:`accordionpanel`,classes:{root:function(e){var t=e.instance,n=e.props;return[`p-accordionpanel`,{"p-accordionpanel-active":t.active,"p-disabled":n.disabled}]}}}),Q={name:`AccordionPanel`,extends:{name:`BaseAccordionPanel`,extends:k,props:{value:{type:[String,Number],default:void 0},disabled:{type:Boolean,default:!1},as:{type:[String,Object],default:`DIV`},asChild:{type:Boolean,default:!1}},style:Z,provide:function(){return{$pcAccordionPanel:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcAccordion`],computed:{active:function(){return this.$pcAccordion.isItemActive(this.value)},attrs:function(){return c(this.a11yAttrs,this.ptmi(`root`,this.ptParams))},a11yAttrs:function(){return{"data-pc-name":`accordionpanel`,"data-p-disabled":this.disabled,"data-p-active":this.active}},ptParams:function(){return{context:{active:this.active}}}}};function ne(e,n,r,a,s,u){return e.asChild?o(e.$slots,`default`,{key:1,class:S(e.cx(`root`)),active:u.active,a11yAttrs:u.a11yAttrs}):(t(),_(i(e.as),c({key:0,class:e.cx(`root`)},u.attrs),{default:l(function(){return[o(e.$slots,`default`)]}),_:3},16,[`class`]))}Q.render=ne;var re=O.extend({name:`accordion`,style:`
    .p-accordionpanel {
        display: flex;
        flex-direction: column;
        border-style: solid;
        border-width: dt('accordion.panel.border.width');
        border-color: dt('accordion.panel.border.color');
    }

    .p-accordionheader {
        all: unset;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: dt('accordion.header.padding');
        color: dt('accordion.header.color');
        background: dt('accordion.header.background');
        border-style: solid;
        border-width: dt('accordion.header.border.width');
        border-color: dt('accordion.header.border.color');
        font-weight: dt('accordion.header.font.weight');
        border-radius: dt('accordion.header.border.radius');
        transition:
            background dt('accordion.transition.duration'),
            color dt('accordion.transition.duration'),
            outline-color dt('accordion.transition.duration'),
            box-shadow dt('accordion.transition.duration');
        outline-color: transparent;
    }

    .p-accordionpanel:first-child > .p-accordionheader {
        border-width: dt('accordion.header.first.border.width');
        border-start-start-radius: dt('accordion.header.first.top.border.radius');
        border-start-end-radius: dt('accordion.header.first.top.border.radius');
    }

    .p-accordionpanel:last-child > .p-accordionheader {
        border-end-start-radius: dt('accordion.header.last.bottom.border.radius');
        border-end-end-radius: dt('accordion.header.last.bottom.border.radius');
    }

    .p-accordionpanel:last-child.p-accordionpanel-active > .p-accordionheader {
        border-end-start-radius: dt('accordion.header.last.active.bottom.border.radius');
        border-end-end-radius: dt('accordion.header.last.active.bottom.border.radius');
    }

    .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.color');
    }

    .p-accordionpanel:not(.p-disabled) .p-accordionheader:focus-visible {
        box-shadow: dt('accordion.header.focus.ring.shadow');
        outline: dt('accordion.header.focus.ring.width') dt('accordion.header.focus.ring.style') dt('accordion.header.focus.ring.color');
        outline-offset: dt('accordion.header.focus.ring.offset');
    }

    .p-accordionpanel:not(.p-accordionpanel-active):not(.p-disabled) > .p-accordionheader:hover {
        background: dt('accordion.header.hover.background');
        color: dt('accordion.header.hover.color');
    }

    .p-accordionpanel:not(.p-accordionpanel-active):not(.p-disabled) .p-accordionheader:hover .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.hover.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader {
        background: dt('accordion.header.active.background');
        color: dt('accordion.header.active.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.active.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader:hover {
        background: dt('accordion.header.active.hover.background');
        color: dt('accordion.header.active.hover.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader:hover .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.active.hover.color');
    }

    .p-accordioncontent {
        display: grid;
        grid-template-rows: 1fr;
    }

    .p-accordioncontent-wrapper {
        min-height: 0;
    }

    .p-accordioncontent-content {
        border-style: solid;
        border-width: dt('accordion.content.border.width');
        border-color: dt('accordion.content.border.color');
        background-color: dt('accordion.content.background');
        color: dt('accordion.content.color');
        padding: dt('accordion.content.padding');
    }
`,classes:{root:`p-accordion p-component`}}),$={name:`Accordion`,extends:{name:`BaseAccordion`,extends:k,props:{value:{type:[String,Number,Array],default:void 0},multiple:{type:Boolean,default:!1},lazy:{type:Boolean,default:!1},tabindex:{type:Number,default:0},selectOnFocus:{type:Boolean,default:!1},expandIcon:{type:String,default:void 0},collapseIcon:{type:String,default:void 0},activeIndex:{type:[Number,Array],default:null}},style:re,provide:function(){return{$pcAccordion:this,$parentInstance:this}}},inheritAttrs:!1,emits:[`update:value`,`update:activeIndex`,`tab-open`,`tab-close`,`tab-click`],data:function(){return{d_value:this.value}},watch:{value:function(e){this.d_value=e},activeIndex:{immediate:!0,handler:function(e){this.hasAccordionTab&&(this.d_value=this.multiple?e?.map(String):e?.toString())}}},methods:{isItemActive:function(e){return this.multiple?this.d_value?.includes(e):this.d_value===e},updateValue:function(e){var t=this.isItemActive(e);this.multiple?t?this.d_value=this.d_value.filter(function(t){return t!==e}):this.d_value?this.d_value.push(e):this.d_value=[e]:this.d_value=t?null:e,this.$emit(`update:value`,this.d_value),this.$emit(`update:activeIndex`,this.multiple?this.d_value?.map(Number):Number(this.d_value)),this.$emit(t?`tab-close`:`tab-open`,{originalEvent:void 0,index:Number(e)})},isAccordionTab:function(e){return e.type.name===`AccordionTab`},getTabProp:function(e,t){return e.props?e.props[t]:void 0},getKey:function(e,t){return this.getTabProp(e,`header`)||t},getHeaderPT:function(e,t){var n=this;return{root:c({onClick:function(e){return n.onTabClick(e,t)}},this.getTabProp(e,`headerProps`),this.getTabPT(e,`header`,t)),toggleicon:c(this.getTabProp(e,`headeractionprops`),this.getTabPT(e,`headeraction`,t))}},getContentPT:function(e,t){return{root:c(this.getTabProp(e,`contentProps`),this.getTabPT(e,`toggleablecontent`,t)),transition:this.getTabPT(e,`transition`,t),content:this.getTabPT(e,`content`,t)}},getTabPT:function(e,t,n){var r=this.tabs.length,i={props:e.props||{},parent:{instance:this,props:this.$props,state:this.$data},context:{index:n,count:r,first:n===0,last:n===r-1,active:this.isItemActive(`${n}`)}};return c(this.ptm(`accordiontab.${t}`,i),this.ptmo(this.getTabProp(e,`pt`),t,i))},onTabClick:function(e,t){this.$emit(`tab-click`,{originalEvent:e,index:t})}},computed:{tabs:function(){var e=this;return this.$slots.default().reduce(function(t,n){return e.isAccordionTab(n)?t.push(n):n.children&&n.children instanceof Array&&n.children.forEach(function(n){e.isAccordionTab(n)&&t.push(n)}),t},[])},hasAccordionTab:function(){return this.tabs.length}},components:{AccordionPanel:Q,AccordionHeader:Y,AccordionContent:K,ChevronUpIcon:L,ChevronRightIcon:I}};function ie(e,n,r,u,d,p){var g=s(`AccordionHeader`),v=s(`AccordionContent`),y=s(`AccordionPanel`);return t(),f(`div`,c({class:e.cx(`root`)},e.ptmi(`root`)),[p.hasAccordionTab?(t(!0),f(h,{key:0},a(p.tabs,function(n,r){return t(),_(y,{key:p.getKey(n,r),value:`${r}`,pt:{root:p.getTabPT(n,`root`,r)},disabled:p.getTabProp(n,`disabled`)},{default:l(function(){return[m(g,{class:S(p.getTabProp(n,`headerClass`)),pt:p.getHeaderPT(n,r)},{toggleicon:l(function(a){return[a.active?(t(),_(i(e.$slots.collapseicon?e.$slots.collapseicon:e.collapseIcon?`span`:`ChevronDownIcon`),c({key:0,class:[e.collapseIcon,a.class],"aria-hidden":`true`},{ref_for:!0},p.getTabPT(n,`headericon`,r)),null,16,[`class`])):(t(),_(i(e.$slots.expandicon?e.$slots.expandicon:e.expandIcon?`span`:`ChevronUpIcon`),c({key:1,class:[e.expandIcon,a.class],"aria-hidden":`true`},{ref_for:!0},p.getTabPT(n,`headericon`,r)),null,16,[`class`]))]}),default:l(function(){return[n.children&&n.children.headericon?(t(),_(i(n.children.headericon),{key:0,isTabActive:p.isItemActive(`${r}`),active:p.isItemActive(`${r}`),index:r},null,8,[`isTabActive`,`active`,`index`])):x(``,!0),n.props&&n.props.header?(t(),f(`span`,c({key:1,ref_for:!0},p.getTabPT(n,`headertitle`,r)),C(n.props.header),17)):x(``,!0),n.children&&n.children.header?(t(),_(i(n.children.header),{key:2})):x(``,!0)]}),_:2},1032,[`class`,`pt`]),m(v,{pt:p.getContentPT(n,r)},{default:l(function(){return[(t(),_(i(n)))]}),_:2},1032,[`pt`])]}),_:2},1032,[`value`,`pt`,`disabled`])}),128)):o(e.$slots,`default`,{key:1})],16)}$.render=ie;var ae={class:`cat`},oe={class:`glass card`},se={class:`answer`},ce=b(p({__name:`FaqView`,setup(r){let i=e([]),o=e(!0),s=y(()=>{let e=new Map;for(let t of i.value){let n=t.category||`General`;e.has(n)||e.set(n,[]),e.get(n).push(t)}return[...e.entries()]});return n(async()=>{try{let{data:e}=await j.faq();i.value=Array.isArray(e)?e:[]}finally{o.value=!1}}),(e,n)=>(t(),f(`div`,null,[m(N,{title:`FAQ`,subtitle:`Answers to common questions`}),!o.value&&!i.value.length?(t(),_(P,{key:0,title:`No FAQs yet`,text:`Check back soon or open a support ticket.`})):x(``,!0),(t(!0),f(h,null,a(s.value,([e,n])=>(t(),f(`div`,{key:e,class:`block`},[d(`h3`,ae,C(e),1),d(`div`,oe,[m(g($),null,{default:l(()=>[(t(!0),f(h,null,a(n,e=>(t(),_(g(Q),{key:e.id,value:e.id},{default:l(()=>[m(g(Y),null,{default:l(()=>[v(C(e.question),1)]),_:2},1024),m(g(K),null,{default:l(()=>[d(`div`,se,C(e.answer),1)]),_:2},1024)]),_:2},1032,[`value`]))),128))]),_:2},1024)])]))),128))]))}}),[[`__scopeId`,`data-v-89c6060c`]]);export{ce as default};