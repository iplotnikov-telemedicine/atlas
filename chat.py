from jinja2 import Template


def render_message(rec):
    username = rec.get('USERNAME')
    message = rec.get('COMMENT')
    if message:
        message = message.replace(' ', '&nbsp;').replace('\n', '<br>')
    date_time = rec.get('DATE_TIME')
    userrights = rec.get('USERRIGHTS')
    if userrights == 'standard':
        background_color = '#1f2229'
        position = 'left'
        align_self = 'flex-start'
    else:
        background_color = '#1f2229'
        position = 'right'
        align_self = 'flex-end'
    return f''' 
        <div class="username" style="margin-bottom: 1em; align-self: {align_self}; overflow: hidden;">
            <div class="param_name"><p align="{position}" style="font-family: Tele2 TextSans;
                font-size: 0.7rem; margin-bottom: 2px; color: white;">{username}</p>
            </div>
            <div class="message" style="border: 0px solid black; border-radius: 15px;
            background-color: {background_color}; padding: 0.7em; padding-bottom: 0;">
                <p style="margin-bottom: 4px; margin-top: 0; margin-left: 4px; margin-right: 4px; 
                font-family: Tele2 TextSans; color: white;">{message}</p>
                <p align="right" style="font-family: Tele2 TextSans; font-size: 0.6rem; color: grey; 
                margin: 0;">{date_time}</p>
            </div>
        </div>
        '''


def render_chat(messages):
    chat = str()
    for msg in messages:
        chat += render_message(msg)
    with open('chat.html') as html:
        template = Template(html.read())
    if not chat:
        nothing_here = '''<p style="font-family: Tele2 TextSans;
            text-align: center; color: #758586">Здесь пока ничего нет 😟</p>'''
    else:
        nothing_here = None
    return template.render(chat=chat, nothing_here=nothing_here)

