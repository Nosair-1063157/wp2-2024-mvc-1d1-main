from flask import Flask, render_template, request, redirect, session, url_for, flash, abort ,Response
import functools
import werkzeug
# from models import json_exporter, database, editor
from models.categorise_questions import Category
from models.editor import *
from models.prompt import *
from models.login import *
from models.question import Question
from models.taxonomy import *
from models.json_exporter import *
from flask_bcrypt import Bcrypt
from math import ceil
from flask_wtf.csrf import CSRFProtect, generate_csrf

app = Flask(__name__)
app.secret_key = "tijdelijk"
json_exporter = JSONExporter()
bcrypt = Bcrypt(app)

# CSRF Protectie
app.config ['WTF_CSRF_TIME_LIMIT'] = 3600
CSRFProtect(app)
@app.context_processor
def inject_csrf_token():
    return {'csrf_token': generate_csrf}


# Bron: https://github.com/Rac-Software-Development/wp-demos
@app.before_request
def access():
    open_routes = ["login", "handle_login", "static", "noaccess"]
    admin_routes = ["editor_overview", "edit_editor", "create_editor"]
    user = session.get("login")
    is_admin = session.get("admin")

    if not user and request.endpoint not in open_routes:
        return redirect(url_for("login"))

    if not is_admin and request.endpoint in admin_routes:
        return redirect(url_for("noaccess"))

@app.route('/')
def overview():
    return redirect('/login')

# Bron: https://dev.to/dev0928/how-to-customize-python-flask-web-application-error-pages-3b25
# Error pages
@app.route("/simulate404")
def simulate404():
    abort(404)
    return render_template("noaccess.html")

@app.route("/simulate500")
def simulate500():
    abort(500)
    return render_template("noaccess.html")

@app.errorhandler(404)
def not_found_error(error):
    return render_template('noaccess.html'), 404

@app.errorhandler(werkzeug.exceptions.HTTPException)
def internal_error(error):
    return render_template('noaccess.html'), 500

# Bron: https://realpython.com/introduction-to-flask-part-2-creating-a-login-page/
# Bron: https://www.fastapitutorial.com/blog/fastapi-jinja-login/

@app.route('/login', methods=['GET','POST'], endpoint='login')
def login():
    if request.method == 'POST':
        # Get the data from the form
        login_email = request.form.get('login')
        login_password = request.form.get('password')

        if not login_email or not login_password:
            return render_template('loginpage.html', error="Vul alle velden in")

        # Check if user excists in database
        login_model = Login()
        user = login_model.load_data_by_email(login_email)

        if user:  # If a user is in database
            hashed_password = user['hashed_password']
            if bcrypt.check_password_hash(hashed_password, login_password):
                session['login'] = user['login']  # Save user in session
                session['display_name'] = user['display_name']
                session['user_id'] = user['user_id']
                session['admin'] = user['admin']
                return redirect('/homepage')

    return render_template('loginpage.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Bron: https://blog.teclado.com/protecting-endpoints-in-flask-apps-by-requiring-login/
@app.route('/homepage')
def home_page():
    is_admin = session.get("admin")
    display_name = session.get('display_name', "Gebruiker")
    question_model = Question()
    uncategorized = question_model.get_uncategorized_questions()
    uncategorized = uncategorized[:10]
    return render_template("homepage.html", display_name=display_name,uncategorized=uncategorized,is_admin=is_admin)


@app.route("/noaccess")
def noaccess():
    return render_template("noaccess.html")


@app.route('/prompt_overview')
def prompt_overview():
    page = request.args.get('page', 1, type=int)
    order = request.args.get('order')
    order_param = request.args.get('sort_by')
    user_id_filter = request.args.get('user_id')
    is_admin = session.get("admin")

    # Get prompts from database with filters
    prompt_model = Prompt()
    prompts, total_count = prompt_model.read_prompts(order, order_param, user_id=user_id_filter, page=page)
    
    # Calculate total pages
    per_page = 10  # Number of items per page
    total_pages = (total_count + per_page - 1) // per_page

    return render_template("prompt_overview.html",
                         prompts=prompts,
                         param=order_param,
                         order=order,
                         selected_user=user_id_filter,
                         is_admin=is_admin,
                         page=page,
                         total_pages=total_pages,
                         sort_by=order_param
                         )

@app.route('/create_prompt', methods=['GET', 'POST'])
def create_prompt():
    is_admin = session.get("admin")
    if request.method == 'POST':
        prompt = request.form.get('Prompt')
        prompt_title = request.form.get('Prompt_Title')
        # replace V
        questions_count= 0
        questions_correct =0
        user_id = session.get("user_id", 1)
        prompt_model = Prompt()
        created_prompt = prompt_model.create_prompt(prompt,prompt_title,user_id,questions_count,questions_correct)
        if created_prompt:
            return redirect('/prompt_overview')
    else:
        return render_template('create_prompt.html', is_admin=is_admin)

@app.route('/menu')
def menu():
    return render_template("base.html")

@app.route('/taxonomie/prompt_id=<int:prompt_id>', methods=['GET'])
def taxonomie_prompt(prompt_id):
    is_admin = session.get("admin")
    prompt_model = Prompt()

    prompt = prompt_model.get_prompt_by_id(prompt_id)

    if prompt:
        taxonomies = prompt_model.get_taxonomies_for_prompt(prompt_id)
        return render_template("taxonomie.html", prompt_text=prompt['prompt'], taxonomies=taxonomies, is_admin=is_admin)
    else:
        return render_template('taxonomie.html', error="Prompt niet gevonden.", is_admin=is_admin)



@app.route('/editor_overview', endpoint='editor_overview')
def editor_overview():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    filter_admin = request.args.get('filter_admin', '')
    search_name = request.args.get('search_name', '')
    search_login = request.args.get('search_login', '')
    sort_name = request.args.get('sort_name', '')
    is_admin = session.get("admin")

    editor_model = Editor()
    users, total_count = editor_model.view_editors(page=page, per_page=per_page, search_name=search_name,
                                                   search_login=search_login, filter_admin=filter_admin, sort_name=sort_name)

    # Calculate total pages
    total_pages = (total_count + per_page - 1) // per_page

    return render_template('editor_overview.html',
                           users=users,
                           is_admin=is_admin,
                           page=page,
                           total_pages=total_pages,
                           search_name=search_name,
                           search_login=search_login,
                           filter_admin=filter_admin,
                           sort_name=sort_name)


@app.route('/create_editor', methods=['GET', 'POST'])
def create_editor():
    is_admin = session.get("admin")
    if request.method == 'POST':
        display_name = request.form.get('display_name')
        email = request.form.get('login')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin')
        editor_model = Editor()
        created_editor = editor_model.create_editor(display_name = display_name, password = password, login = email, is_admin = is_admin)
        if created_editor['success']:
            return redirect('/editor_overview')
        else:
            flash(created_editor['message'], category="error")
            return render_template(
                'create_editor.html',
                is_admin=is_admin,
                error_message=created_editor['message'],
                display_name=display_name,
                login=email
            )
    else:
        return render_template('create_editor.html', is_admin=is_admin)


@app.route('/edit_editor', defaults={'user_id': None}, methods=['GET', 'POST'])
@app.route('/edit_editor/<int:user_id>', methods=['GET', 'POST'])
def edit_editor(user_id):
    editor_model = Editor()
    is_admin = session.get("admin")

    if request.method == 'POST':
        display_name = request.form['display_name']
        login = request.form['login']
        password = request.form['password']
        is_admin = request.form['is_admin']

        updated = editor_model.edit_editor(
            user_id=user_id,
            display_name=display_name,
            password=password,
            login=login,
            is_admin=is_admin
        )
        if updated:
            return redirect('/editor_overview')
        else:
            return "Error updating user", 500
    read_editor = editor_model.read_editor(user_id)

    if read_editor:
        return render_template('edit_editor.html', user=read_editor, is_admin=is_admin)
    else:
        return "Error 404, User not found", 404

@app.route('/delete_editor/<int:user_id>', methods=['POST'])
def delete_editor(user_id):
    editor = Editor()

    success = editor.delete_editor(user_id)
    if success:
        flash("Gebruiker successvol verwijderd", "success")

    else:
        flash("Gebruiker kan niet worden verwijderd", "error")
    return redirect(url_for('editor_overview'))


@app.route('/prompt_details', methods=['GET', 'POST'])
def prompt_details():
    is_admin = session.get("admin")
    if request.method == 'GET':
        prompts_id = request.args['prompts_id']
        prompt_model = Prompt()
        prompt = prompt_model.read_prompt(prompts_id)
        questions_count = prompt['questions_count']
        questions_correct = prompt['questions_correct']

        incorrect_questions = prompt_model.calculate_incorrect(questions_count, questions_correct)
        return render_template("prompt_details.html", prompt=prompt, incorrect_questions=incorrect_questions, is_admin=is_admin)

@app.route('/delete_task/<int:prompts_id>', methods=['POST', 'GET'])
def delete_task(prompts_id):
    prompt_model = Prompt()
    prompt_model.delete_prompt(prompts_id)
    return redirect('/prompt_overview')


@app.route('/taxonomy_update/<int:taxonomy_id>', methods=['GET', 'POST'])
def taxonomy_update(taxonomy_id):
    taxonomy_model = Taxonomy()
    taxonomy = taxonomy_model.read_ai_taxonomy(taxonomy_id)
    is_admin = session.get("admin")
    if request.method == 'POST':
        teacher_taxonomy= request.form.get('teacher_taxonomy')
        try:
            taxonomy_model.update_taxonomy(taxonomy_id,teacher_taxonomy)
            taxonomy= taxonomy_model.read_ai_taxonomy(taxonomy_id)
            average_taxonomy= taxonomy_model.average_taxonomy_calc(taxonomy_id)
            if average_taxonomy:
                taxonomy['average_taxonomy'] = average_taxonomy
                taxonomy_model.update_taxonomy_average(taxonomy_id,average_taxonomy)
            message= "Opgeslagen"
        except Exception as e:
            message= f"error: {e}"
        return render_template("taxonomy_update.html", taxonomy=taxonomy, message=message, is_admin=is_admin)

    return render_template("taxonomy_update.html", taxonomy=taxonomy, message=None, is_admin=is_admin)


@app.route('/questions', methods=['GET'])
def questions():
    is_admin = session.get("admin")
    search_query = request.args.get('query', '')
    user_id = request.args.get('user_id', None)
    order = request.args.get('order', 'desc')
    page = int(request.args.get('page', 1, type=int))
    per_page = 10  
   
    questions_model = Question()
    
    total_questions = questions_model.get_total_questions(search_query=search_query, user_id=user_id)
    total_pages = ceil(total_questions / per_page)
    
    all_questions = questions_model.read_questions(
        search_query=search_query,
        user_id=user_id,
        order=order,
        page=page,
        per_page=per_page
    )
    
    return render_template(
        "questions.html",
        questions=all_questions,
        current_order=order,
        search_query=search_query,
        current_user_id=user_id,
        is_admin=is_admin,
        current_page=page,
        per_page=per_page,
        total_pages=total_pages 
    )
@app.route('/create_question', methods=['GET', 'POST'])
def create_question():
    is_admin = session.get("admin")
    if request.method == 'POST':
        questions_id = request.form['questions_id']
        question = request.form['question']
        prompts_id = request.form['prompts_id']
        user_id = request.form['user_id']
        taxonomy_bloom = request.form['taxonomy_bloom']
        rtti = request.form['rtti']
        exported = 1 if 'exported' in request.form else 0

        question_model = Question()
        try:
            question_model.create_question(questions_id, question, prompts_id, taxonomy_bloom, rtti, exported, user_id)
            return redirect('/questions')
        except Exception as e:
            return f"Fout bij toevoegen: {e}", 400

    editor_model = Editor()
    users = editor_model.view_editors()
    return render_template('create_question.html', users=users, is_admin=is_admin)

@app.route('/delete_question/<string:question_id>', methods=['POST'])
def delete_question(question_id):
    question_model = Question()
    question_model.delete_question(question_id)
    return redirect('/questions')

@app.route('/taxonomy_overview')
def taxonomy_overview():
    taxonomy_model= Taxonomy()
    all_taxonomy = taxonomy_model.get_all_taxonomy()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(all_taxonomy) + per_page - 1) // per_page
    taxonomy_page = all_taxonomy[start:end]
    is_admin = session.get("admin")
    return render_template("taxonomy_overview.html", all_taxonomy=all_taxonomy, taxonomy_page=taxonomy_page,total_pages=total_pages,page=page, is_admin=is_admin)


@app.route('/edit_question/<string:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    question_model = Question()
    is_admin = session.get("admin")
    if request.method == 'POST':
        question_data = {
            'question_id': request.form['question_id'],
            'prompts_id': request.form['prompts_id'],
            'user_id': request.form['user_id'],
            'question': request.form['question'],
            'taxonomy_bloom': request.form['taxonomy_bloom'],
            'rtti': request.form['rtti'],
            'exported': 'exported' in request.form
        }

        try:
            question_model.update_question(question_data)
            return redirect(url_for('questions'))
        except Exception as e:
            return f"Error updating question: {e}", 400

    question = question_model.get_question_by_id(question_id)
    return render_template('edit_question.html', question=question, is_admin=is_admin)


@app.route('/export_all', methods=['GET'])
def export_all():
    json_content = json_exporter.get_all_questions_json()
    return Response(
        json_content,
        mimetype='application/json',
        headers={"Content-Disposition": "attachment; filename=all_questions.json"}
    )

@app.route('/export_question/<question_id>', methods=['GET'])
def export_question(question_id):
    json_content = json_exporter.get_question_json(question_id)

    if json_content is None:
        flash("Er is iets fout gegaan. dit kan komen omdat deze vraag nog niet gecategoriseerd is",
              "error")
        return redirect(url_for('questions'))
    else:
        return Response(
            json_content,
            mimetype='application/json',
            headers={"Content-Disposition": f"attachment; filename=gexeporteerde_vragen.json"}
        )

@app.route('/category', methods=['GET', 'POST'])
def category():
    question_id= request.args.get('question_id', default=None)
    questions_model = Question()
    prompt_model = Prompt()
    taxonomy_model = Taxonomy()

    categorise_questions_model = Category()
    all_questions = questions_model.get_all_questions()
    all_prompts = prompt_model.get_all_prompts()
    all_taxonomies = taxonomy_model.get_all_taxonomy()
    is_admin = session.get("admin")
    if request.method == 'POST':

        selected_question_id = request.form.get('question')
        selected_prompt_id = request.form.get('prompts')
        selected_taxonomy_id = request.form.get('taxonomy')
        selected_ai_choice = request.form.get('ai_choice')
        if not selected_question_id or not selected_prompt_id or not selected_taxonomy_id:
            return render_template("categorise_question.html", all_questions=all_questions, all_prompts=all_prompts, all_taxonomies=all_taxonomies, is_admin=is_admin,preselect_q_id=question_id)

        selected_question = categorise_questions_model.get_selected_question(selected_question_id)
        selected_prompt =categorise_questions_model.get_selected_prompt(selected_prompt_id)
        selected_taxonomy = categorise_questions_model.get_selected_taxonomy(selected_taxonomy_id)
        if not selected_question or not selected_prompt:
            return "Invalid data provided", 400

        #geef api request regels aan
        if selected_taxonomy == "rtti":
            selected_prompt = """
                THIS IS AN API REQUEST. USE RTTI TAXONOMY. DO NOT USE " INSIDE OF THE "uitleg" AND DO NOT USE SINGLE QUOTES TO DEFINE KEYS!!! Analyze the question and categorize it using the RTTI taxonomy. Provide one category per question, along with an explanation, in the following JSON format:
                Here is the RTTI taxonomy:
                1. **Reproductie**: Questions that involve recalling and reproducing memorized material or facts
                2. **Toepassing 1**: Questions that involve applying learned material in familiar, practiced situations
                3. **Toepassing 2**: Questions that involve applying learned material in new, unfamiliar situations.
                4. **Inzicht**: Questions where the student must construct their own method, integrate knowledge, or reason through a solution.
                
                **Instructions**:
                1. Analyze the given question.
                2. Match it to one RTTI category based on the definitions.
                3. Provide the response in the required JSON format.
                
            """ + f"**Question**: {selected_prompt}"
        else:
            selected_prompt = ("THIS IS AN API REQUEST." +
                               f"USE {selected_taxonomy} TAXONOMY. DONT USE \" INSIDE OF THE \"uitleg\" AND "
                               f"DONT USE SINGLE QUOTES TO DEFINE KEYS!!! Analyze the question and provide a single {selected_taxonomy} category and explanation for the categorization."
                               f"prompt: {selected_prompt}"
                               )
        if selected_ai_choice =="ollama":
            returned_question = categorise_questions_model.categorise_question_ollama(selected_question, selected_prompt)
        elif selected_ai_choice =="chatgpt":
            returned_question = categorise_questions_model.categorise_question(selected_question, selected_prompt)
        else:
            returned_question = categorise_questions_model.categorise_question(selected_question, selected_prompt)

        if isinstance(returned_question, (dict, list)):
            categorized_question_json = json.dumps(returned_question)
            return redirect(url_for('categorized_question', result=categorized_question_json, question_id=selected_question_id,prompt_id=selected_prompt_id))
        else:
            flash("Er is iets fout gegaan. Run de prompt opnieuw, herschrijf of gebruik een andere prompt", "error")
    return render_template("categorise_question.html", all_questions=all_questions, all_prompts=all_prompts, all_taxonomies=all_taxonomies, is_admin=is_admin,preselect_q_id=question_id)

@app.route('/upload_json', methods=['POST'])
def upload_json():
    if 'json_file' not in request.files:
        flash('Geen bestand gekozen', 'error')
        return redirect(url_for('questions'))

    json_file = request.files['json_file']

    if json_file and json_file.filename.endswith('.json'):
        try:
            file_data = json_file.read().decode('utf-8')
            questions_data = json.loads(file_data)

            user_id = get_current_user_id()

            if not questions_data:
                flash('Het bestand bevat geen gegevens', 'error')
                return redirect(url_for('questions'))

            for item in questions_data:
                question = item.get("question")
                if not question:
                    continue

                question_id = item.get("question_id", None)
                prompts_id = item.get("question_index", None)

                taxonomy_bloom = item.get("taxonomy_bloom")
                rtti = item.get("rtti")

                answer = item.get("answer", None)
                exported = True if answer else False

                question_instance = Question()
                question_instance.create_question(
                    questions_id=question_id,
                    question=question,
                    prompts_id=prompts_id,
                    taxonomy_bloom=taxonomy_bloom,
                    rtti=rtti,
                    exported=exported,
                    user_id=user_id
                )

            flash('Vragen geupload!', 'success')
            return redirect(url_for('questions'))

        except json.JSONDecodeError:
            flash('Er is een error ', 'error')
            return redirect(url_for('questions'))
        except Exception as e:
            flash(f'Er is een error: {e}', 'error')
            return redirect(url_for('questions'))
    else:
        flash('Ongeldig bestandstype, Alleen JSON', 'error')
        return redirect(url_for('questions'))


def get_current_user_id():
    return session.get('user_id')

@app.route('/categorized_question/result', methods=['GET','POST'])
def categorized_question():
    questions_model = Question()
    prompt_model = Prompt()
    taxonomy_model = Taxonomy()

    all_taxonomies = taxonomy_model.get_all_taxonomy()
    all_questions = questions_model.get_all_questions()
    all_prompts = prompt_model.get_all_prompts()

    new_categorized_question = request.args.get('result')
    selected_question_id = request.args.get('question_id')
    selected_prompt_id = request.args.get('prompt_id')

    # selected_taxonomy_id = request.args.get('taxonomy_id')


    is_admin = session.get("admin")

    if request.method == 'POST':
        action = request.form.get('action')

        if action:
            approving_process_prompt = prompt_model.prompt_approving(selected_prompt_id, action,new_categorized_question, selected_question_id)
            answer = json.loads(new_categorized_question)
            question_category = answer["categorie"]
            approving_process_question = questions_model.category_approving(selected_question_id, question_category, action)

            if approving_process_prompt and approving_process_question:
                flash("Het is gelukt! De vraag is gecategoriseerd.", "success")

        return render_template("categorise_question.html", all_questions=all_questions, all_prompts=all_prompts, all_taxonomies=all_taxonomies, is_admin=is_admin)

    new_categorized_question = json.loads(new_categorized_question)
    return render_template('categorized_question_check.html', categorized_question=new_categorized_question, is_admin=is_admin)

@app.route('/support')
def support():
    is_admin = session.get("admin")
    return render_template('support.html', is_admin=is_admin)

@app.route('/support/vragen')
def support_vragen():
    is_admin = session.get("admin")
    return render_template('support_vragen.html', is_admin=is_admin)

@app.route('/support/prompts')
def support_prompts():
    is_admin = session.get("admin")
    return render_template('support_prompts.html', is_admin=is_admin)

@app.route('/support/redacteuren')
def support_redacteuren():
    is_admin = session.get("admin")
    return render_template('support_redacteuren.html', is_admin=is_admin)


if __name__ == "__main__":
    app.run()