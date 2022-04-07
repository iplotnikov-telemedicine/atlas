import streamlit as st



def custom_caption(text):
    return f'''
            <div class="custom_caption"><p style="font-family: Tele2 TextSans;
                font-size: 14px; margin-bottom: 0rem; color: #515358;">{text}</p></div>'''


def captions_block(*captions):
    captions_block = str()
    for caption in captions:
        captions_block += custom_caption(caption)
    return st.markdown(f'''<div class="captions_block" style="margin-bottom: 15px;">{captions_block}</div>''', unsafe_allow_html=True) 


def custom_checkbox(param_name, param_value):
    aria_checked = ('✓️' if param_value else '✗️')
    return st.markdown(f'''
        <div class="custom_checkbox">
            <p style="margin-top: 0rem">
                <span style="padding: 6px; font-family: Tele2 TextSans;
                font-weight: bold; font-size: 1rem;">{aria_checked + '  '}</span>
                <span style="padding-left: 2px; font-family: Tele2 TextSans;
                font-size: 1rem;">{param_name}</span>
        </div>

    ''', unsafe_allow_html=True)


def show_msg_count(msg_count):
    # 353b49
    if msg_count > 0:
        background_color = '#00b5ef'
        return st.markdown(f'''
        <div class="msg_count">
            <p>
                <span style="position: absolute; top: 2.1em; left: 7.3em; border_radius: 25px; 
                background_color: {background_color}; font-family: Tele2 TextSans; color: white; 
                padding-right: 7px; padding-left: 7px; font-size: 0.8em;">{msg_count}</span>
            </p>
        </div>
        ''', unsafe_allow_html=True)
    else:
        background_color = '#353b49'
        return None
    

def custom_param(param_name, param_value):
    return st.markdown(f'''
        <div class="fixed_param">
            <label class="css-1t3u4t2 effi0qh0" style="margin-bottom: 7px; font-size: 14px;">{param_name}</label>
            <div class="fixed_value"><p style="font-family: Tele2 DisplayStencil; font-size: 14px; 
                border: 1px solid; border-radius: 5px; border-color: #34373d; 
                padding: 0.7em;">{param_value}</p>
            </div>
        </div>
        ''', unsafe_allow_html=True)


def custom_tariff(param_value):
    return st.markdown(f'''
        <div class="fixed_param" style="height: 48px;">
            <div class="fixed_value"><p style="font-family: Tele2 DisplayStencil; font-size: 12; 
                border: 1px solid; border-radius: 5px; border-color: #34373d; 
                padding: 0.7em;">{param_value}</p>
            </div>
        </div>
        ''', unsafe_allow_html=True)


def show_container(text):
    return st.markdown(f'''
        <div class="username" style="margin-bottom: 1em">
            <div class="message" style="border: 0px solid #0d1012; border-radius: 5px;
            background-color: #17191f; padding: 0.7em; ">
                <p style="margin: 0">{text}</p>
            </div>
        </div>
        ''', unsafe_allow_html=True)


def stylize_scenario(scenario_name):
    return st.markdown(f'''
        <div class="scenario" style="position: absolute; width: 110%; border: 0px solid #0d1012; border-radius: 5px;
        background-color: transparent; padding: 0.5em; padding-left: 0.7em; height: 70px; overflow: hidden;
        border: 1px solid rgba(245, 245, 244, 0.2);">
            <p style="margin-bottom: 2px; width: 210px; font-size: 1vw;">{scenario_name}</p>
        </div>
        ''', unsafe_allow_html=True)


def stylize_action(action, tariff, changes_dict):
    changes_str = str()
    for change in changes_dict:
        changes_str += f'''<small><p>{change[0]}: {change[1]} -> {change[2]}</p></small>'''
    return st.markdown(f'''
        <div class="action" style="width: 110%; border: 0px solid #0d1012; border-radius: 5px;
        background-color: transparent; padding: 0.5em; padding-left: 0.7em; height: auto; overflow: hidden;
        border: 1px solid rgba(245, 245, 244, 0.2);">
            <p style="margin-bottom: 2px; width: 210px; font-size: 0.8vw;">{action}</p>
            <p style="margin-bottom: 2px; width: 210px; font-size: 0.6vw; font_weight: bold;">{tariff}</p>
            {changes_str}
        </div>
        ''', unsafe_allow_html=True)


def stylize_header(text):
    return st.markdown(f'''<div style="font-family: Tele2 DisplayStencil; text-align: left; margin-top: 1em; margin-bottom: 1em;
        font-weight: bold; font-size: 1.5vw; color: white; z-index: 999; vertical-align: bottom;
        z-index: 1;">{text}</div>''', unsafe_allow_html=True)   


def stylize_gb(text):
    return st.markdown(f'''<div class="stylized" style="font-family: Tele2 DisplayStencil; text-align: center; 
    font-weight: bold; font-size: 1.3vw; width: 100%; position: absolute; top: 3em;
    height: 100%;">{text}</div>''', unsafe_allow_html=True)


def stylize_voice(text):
    return st.markdown(f'''<div class="stylized" style="font-family: Tele2 DisplayStencil; text-align: center; 
    padding-top: 0.6em; font-weight: bold; font-size: 1.3vw; ">{text}</div>''', unsafe_allow_html=True)
                

def empty_label():
    return st.markdown(f'''
            <div class="empty_label">
                <div class="param_name"><p style="font-family: Tele2 TextSans;
                    font-size: 0.8rem; margin-bottom: 0.3rem; color: #a2a2a5;">&nbsp;</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)


@st.experimental_memo
def draw_sim(row_num, col_num, tar, rec, selected=True, valid=True, is_lightened=False):
    tooltip_text = str()
    fee = (str(rec.get('FEE')) if rec.get('FEE') else rec.get('CLASSIC_MINUTE_PRICE'))
    fee_after_disc = str(rec.get('FEE_AFTER_DISCOUNT'))
    
    if rec.get('IS_INSTALLMENT'):
        inst_mark = '🅿️'
        tooltip_text += f'''🅿️ - нужна рассрочка\n'''
    else:
        inst_mark = ''

    if rec.get('IS_MDP'):
        mdp_mark = 'Ⓜ️'
        tooltip_text += f'''Ⓜ️ - нужен МАП\n'''
    else:
        mdp_mark = ''

    if rec.get('IS_CBM_CHANGE'):
        cbm_mark = '🎀'
        tooltip_text += f'''🎀 - нужна смена на акционные\n'''
    else:
        cbm_mark = ''
    valid_mark = ('&nbsp;' if valid else '🚫')
    mark = ('✔️  ' if fee else '&nbsp;')
    fee = (str(fee) if fee else '')
    slash_fee = ('/' + str(fee_after_disc) if rec.get('IS_FEE_DISCOUNT') else '')
    sim_color = '#1f2229'
    if is_lightened: 
        opacity = 1
    else:
        opacity = 0.4
    if selected:
        color_attr = 'background-color: #11ffee00'
    else: 
        color_attr = ''
    # if locked:
    #     margin_attr = ''
    # else: 
    #     margin_attr = ''
    tar_watermark = '<br>'.join(word for num, word in enumerate(tar.split(' ')))
    return f'''
    <div class="sim_outside" data-testid="{row_num}{col_num}"
        style="opacity: {opacity}; {color_attr}; margin-bottom: 2px; ">
            <div class="sim_inside" style="overflow-wrap: break-word; aspect-ratio: 205 / 135; 
            background-color: {sim_color}; min-height: 5em;">
                <p align="right" style="position: absolute; z-index: -1; left: 130px; font-size: 0.9vw;">{valid_mark}</p>
                <p align="center" style="position: absolute; z-index: -2; -webkit-transform: rotate(-45deg); 
                top: 1.6em; left: 3.7em; overflow-wrap: break-word; color: #45484e; 
                vertical-align: middle; opacity: 0.8; font-family: Tele2 DisplayStencil; white-space: pre;
                font-weight: bold; font-size: 1.5vw; margin-bottom: 0; line-height: 100%;">{tar_watermark}</p>
                <p align="left" style="font-family: Tele2 DisplayStencil; margin-left: 0.2em;
                font-size: 1.8vw; margin-bottom: 0; vertical-align: top;">{fee}{slash_fee}
                <span style="font-size: 1vw; vertical-align: super;">
                {'₽' if fee and rec.get('TARIFF') != 'Классический' else ''}</span></p>
                <p style="position: absolute; bottom: 10px; font-family: Tele2 DisplayStencil; font-size: 16; 
                margin-bottom: 0; vertical-align: top;"><span align="left">{cbm_mark}{mdp_mark}{inst_mark}</span></p>    
            </div>
    </div>
    '''


def show_tariff_branch(tariff, branch):
    st.markdown(f'''<p style = "font-family: Tele2 DisplayStencil; margin-bottom: 0;
        font-size: 22px; font-weight: bold;">{tariff}</p>''', unsafe_allow_html=True)
    st.markdown(f'''<p style = "font-family: Tele2 TextSans; color: #00b5ef; margin-bottom: 0;
                font-size: 16px; font-weight: regular;">{branch}</p>''', unsafe_allow_html=True)
    