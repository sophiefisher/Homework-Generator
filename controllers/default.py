import random, string
import evaluator as expression_evaluator

class Problem(object):

    def __init__(self,givens,sol_alg):
        self.sol_alg=sol_alg
        self.givens=givens

    def get_solution(self):
        #replace algorithm with givens
        for i in range(len(self.givens)):
            v = "v"  + str(i)
            given = str(self.givens[i])
            self.sol_alg=self.sol_alg.replace(v,given)

        #insert parsing algorithm here
        parser=expression_evaluator.Parser()
        solution=parser.parse(self.sol_alg).evaluate({})
        return solution

def user():
    return dict(form=auth())

@auth.requires_login()
def index():
    return locals()

def student_interface():
    session.jump_back=request.env.request_uri
    student_record=db(db.student.email==auth.user.email).select().last()
    my_courses=db(db.student_course.student_id==student_record.id).select()
    problem_type_courses=db(db.problem_type_course).select()
    #ditionary to associate problem types with classes
    d={}
    for r in problem_type_courses:
        if not d.has_key(r.course_id):
            d[r.course_id]=[]
        d[r.course_id].append(r.problem_type_id)

    score_records=db(db.user_score.user_id==auth.user.id).select()
    problem_type_scores={}
    for r in score_records:
       problem_type_scores[r.problem_type_id]=r.num_solved
    problem_type_attempts={}
    for r in score_records:
        if r.num_solved !=0:
            problem_type_attempts[r.problem_type_id]=round(float(r.num_tries) / r.num_solved, 3)
        else:
            problem_type_attempts[r.problem_type_id]=0
    return locals()

def generator():

    #session.jump_back=request.env.request_uri
    problem_type=db.problem_type(request.args(0))
    last_problem=db((db.problem.user_id==auth.user.id)&\
                    (db.problem.problem_type_id==problem_type)).select().last()
    given_types = db(db.problem_type_given_type.problem_type_id==problem_type.id).select()
    parser=expression_evaluator.Parser()
    
    #generate a new problem if no previous problems of this type exist
    if last_problem is None:
        #generate givens and store in dictionary
        given_name_value = {}
        for given_type in given_types:
            val = random.randint(given_type.lower_bound, given_type.upper_bound)
            given_name_value[given_type.name] = val
            #rec=db.problem_given.insert(given_type_id=given_type.id, given = val)

        #generate problem prompt
        prompt = problem_type.prompt
        for key in given_name_value:
            identity = "{" + key + "}"
            prompt = string.replace(prompt,identity,str(given_name_value[key]))

        #parse problem solution
        sol_alg = problem_type.sol_alg
        for key in given_name_value:
            identity = "{" + key + "}"
            sol_alg = string.replace(sol_alg,identity,str(given_name_value[key]))
        solution=parser.parse(sol_alg).evaluate({})

        #add problem and problem_givens to database
        problem_id=db.problem.insert(user_id=auth.user.id,problem_type_id=problem_type,answered=False,solution=solution)
        for given_type in given_types:
            rec=db.problem_given.insert(given_type_id=given_type.id, given = given_name_value[given_type.name], problem_id = problem_id)

        #add score record to database for new problem
        db.user_score.insert(user_id=auth.user.id,problem_type_id=problem_type.id,num_tries=0,num_solved=0)
    
    #pull last problem from the databse if the problem is not answered
    elif last_problem.answered==False:
        solution = last_problem.solution
        
        prompt = problem_type.prompt
        for given_type in given_types:
            identity = "{" + given_type.name + "}"
            problem_given = db((db.problem_given.given_type_id==given_type.id) & (db.problem_given.problem_id==last_problem.id)).select().last()
            prompt = string.replace(prompt,identity,str(problem_given.given))
    
    #regenerate a new problem if the last problem is answered
    elif last_problem.answered==True:
        #generate givens and store in dictionary
        given_name_value = {}
        for given_type in given_types:
            val = random.randint(given_type.lower_bound, given_type.upper_bound)
            given_name_value[given_type.name] = val
            #rec=db.problem_given.insert(given_type_id=given_type.id, given = val)

        #generate problem prompt
        prompt = problem_type.prompt
        for key in given_name_value:
            identity = "{" + key + "}"
            prompt = string.replace(prompt,identity,str(given_name_value[key]))

        #parse problem solution
        sol_alg = problem_type.sol_alg
        for key in given_name_value:
            identity = "{" + key + "}"
            sol_alg = string.replace(sol_alg,identity,str(given_name_value[key]))
        solution=parser.parse(sol_alg).evaluate({})
        #update problem and problem_givens
        last_problem.update_record(solution=solution)
        for given_type in given_types:
            problem_given = db((db.problem_given.given_type_id==given_type.id) & (db.problem_given.problem_id==last_problem.id)).select().last()
            problem_given.update_record(given = given_name_value[given_type.name])

        #update problem answered
        last_problem.update_record(answered=False)


    row = db((db.user_score.user_id==auth.user.id)&\
             (db.user_score.problem_type_id==problem_type.id)).select().first()
    form=SQLFORM.factory(
        Field('your_answer','decimal(2,10)'))
    form['_style']='background: #F2F2F2; width: 415px; padding: 5px; border-radius: 5px; border:1.5px solid #B6B6B6'
    correct_answer_button=False
    wrong_answer_button=False
    #last_problem.update_record(answered=True)

    if form.process(message_onsuccess=None).accepted:
        row.update_record(num_tries=row.num_tries+1)
        if solution > 0:
            if (form.vars.your_answer>.97*float(solution) and form.vars.your_answer<1.03*float(solution)):
                row.update_record(num_solved=row.num_solved+1)
                correct_answer_button=True
                last_problem.update_record(answered=True)
        elif solution < 0:
            if (form.vars.your_answer<.97*float(solution) and form.vars.your_answer>1.03*float(solution)):
                row.update_record(num_solved=row.num_solved+1)
                correct_answer_button=True
                last_problem.update_record(answered=True)
        if correct_answer_button==False:
            wrong_answer_button=True
            #session.flash='Incorrect!'
            #redirect(URL('generator'))
    return locals()


def teacher_interface():
    session.jump_back=request.env.request_uri
    my_problem_types = db(db.problem_type.teacher_id==auth.user.id).select()
    problem_type_classes={}
    for r in my_problem_types:
        sec_one_classes=[]
        classes=db((db.problem_type_course.problem_type_id==r.id)).select()
        problem_type_classes[r.id]=classes
    problem_type_given_types={}
    for r in my_problem_types:
        given_types = db(db.problem_type_given_type.problem_type_id==r.id).select()
        problem_type_given_types[r.id]=given_types
    return locals()


def create_problem():
    #course_query=(db.course.section=='1')
    #db.problem_type.course_id.requires=IS_IN_DB(db(course_query),
    #                                          db.course.id,
    #                                          lambda r: db.course[r.id].name)
    form=SQLFORM(db.problem_type,
                 fields=['name','given_list','prompt','sol_alg'],
                 labels={'name':CAT('Problem', BR(), 'Name'), 'given_list':CAT('List of', BR(), 'Variables'), 'prompt':CAT('Problem', BR(), 'Prompt'), 'sol_alg':CAT('Solution', BR(), 'Algorithm')},submit_button='Create Problem')
    form.vars.teacher_id=auth.user.id
    if form.process().accepted:
        #session.flash='problem added!'
        given_text = form.vars.given_list
        given_list = [x.strip() for x in given_text.split(',')]
        for given in given_list:
            record=db.problem_type_given_type.insert(problem_type_id=form.vars.id,name=given)

        session.flash='problem added!'
        redirect(URL('default','create_problem'))
    return locals()


def remove_class_problem_type():
    r = db.problem_type_course(request.args(0))
    name = r.course_id.name  
    records = db(db.problem_type_course).select()
    for r in records:
        if r.course_id.name==name:
            r.delete_record()
    redirect(URL('default','teacher_interface'))
    
def add_problem_type_classes():
    #course_query=(db.course.section=='1')
    #db.problem_type.course_id.requires=IS_IN_DB(db(course_query),
    #                                          db.course.id,
    #                                          lambda r: db.course[r.id].name)
    
    
    problem_type = db.problem_type(request.args(0))
    problem_type_courses=db(db.problem_type_course.problem_type_id==problem_type.id).select()
    courses=[]
    for r in problem_type_courses:
        courses.append(r.course_id)
    all_courses=db(db.course).select()
    available_courses=[course.id for course in all_courses if course.id not in courses]
    
    c_query=((db.course.id.belongs(available_courses)) & (db.course.section=='1'))
    
    db.problem_type_course.course_id.requires=IS_IN_DB(db(c_query),db.course.id,lambda r: db.course[r.id].name)
    form=SQLFORM.factory(Field('course_id', 'reference course',requires=IS_IN_DB(db(c_query),db.course.id,"%(name)s")),
                 labels={'course_id':'Class'})
    
    if form.process().accepted:
        course_selected = db(db.course.id == form.vars.course_id).select().first()
        all_sections = db(db.course.name==course_selected.name).select()
        for r in all_sections:
            db.problem_type_course.insert(problem_type_id=problem_type.id,
                                          course_id=r.id)
            db.commit()
        session.flash="course added!"
        redirect(URL('default','add_problem_type_classes',args=problem_type.id))
    return locals()


def class_progress():
    teacher_id = db(db.teacher.email==auth.user.email).select().first()
    teacher_sections = db((db.teacher_course.teacher_id==teacher_id.id)).select()
    teacher_courses=[r for r in teacher_sections if r.course_id.section=="1"]
    course_problem_types ={}
    for course in teacher_courses:
        problem_type_courses = db(db.problem_type_course.course_id==course.course_id).select()
        course_problem_types[course.course_id]=problem_type_courses
    return locals()

def problem_statistics():
    course = db.course(request.args(0))
    problem_type = db.problem_type(request.args(1))
    all_course_sections = db(db.course.name==course.name).select(orderby=db.course.section)
    course_section_students = {}
    for section in all_course_sections:
        students = db(db.student_course.course_id==section.id).select()
        course_section_students[section.id]=students
    attempted_problem_type = db(db.user_score.problem_type_id==problem_type.id).select()
    student_stats={}
    for stud in attempted_problem_type:
        stud_email = stud.user_id.email
        stud_rec = db(db.student.email==stud_email).select().first()
        if stud.num_solved!=0:
            avg_attempt=round(float(stud.num_tries) / stud.num_solved, 3)
        elif stud.num_solved==0:
            avg_attempt=0
        student_stats[stud_rec.id]=(avg_attempt,stud.num_solved)
    section_stats={}
    for section in all_course_sections:
        students = course_section_students[section.id]
        total_attempts = 0
        total_solved = 0
        num_attempted=0
        for student_rec in students:
            if student_rec.student_id in student_stats:
                total_attempts+=student_stats[student_rec.student_id][0]
                total_solved+=student_stats[student_rec.student_id][1]
                num_attempted+=1
        if num_attempted !=0:
            avg_attempts = round(total_attempts / num_attempted, 3)
            avg_solved = round(float(total_solved) / num_attempted, 3)
        else:
            avg_attempts = 0
            avg_solved = 0
        section_stats[section.id] = (avg_attempts, avg_solved)
    if len(all_course_sections) > 1:
        class_attempts = 0
        class_solved = 0
        cnum_attempted = 0
        for section in all_course_sections:
            for student_rec in course_section_students[section.id]:
                if student_rec.student_id in student_stats:
                    class_attempts+=student_stats[student_rec.student_id][0]
                    class_solved+=student_stats[student_rec.student_id][1]
                    cnum_attempted+=1
        if cnum_attempted !=0:
            avgclass_attempts = round(class_attempts / cnum_attempted, 3)
            avgclass_solved = round(float(class_solved) / cnum_attempted, 3)
        else:
            avgclass_attempts = 0
            avgclass_solved = 0
    return locals()

def delete_problem_type():
    problem_type = db.problem_type(request.args(0))
    problem_type.delete_record()
    redirect(URL('default','teacher_interface'))

def edit_givens():
    given_type = db.problem_type_given_type(request.args(0))
    problem_type = db.problem_type(request.args(1))
    form = SQLFORM(db.problem_type_given_type, given_type, deletable=False, fields=['lower_bound', 'upper_bound'],showid=False)
    if form.process().accepted:
        response.flash="Sucess!"
    return locals()

def edit_problem_type():
    problem_type = db.problem_type(request.args(0))
    form = SQLFORM(db.problem_type, problem_type, deletable=False, fields=['name', 'prompt', 'sol_alg'],labels={'name':CAT('Problem', BR(), 'Name'), 'prompt':CAT('Problem', BR(), 'Prompt'), 'sol_alg':CAT('Solution', BR(), 'Algorithm')},showid=False)
    db.problem_type.name.label = CAT('My', BR(), 'Label')
    if form.process().accepted:
        response.flash="Sucess!"
    return locals()
