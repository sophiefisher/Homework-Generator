from gluon.tools import Auth, Crud

db=DAL("sqlite://storage.sqlite")
auth=Auth(db)
crud=Crud(db)
auth.define_tables()

#pulled from tracks
db.define_table("advisor",
     Field("first_name","string"),
     Field("last_name","string"),
     Field("email","string"),
     format='%(first_name)s %(last_name)s')


#pulled from tracks
db.define_table("student",
     Field("first_name","string"),
     Field("last_name","string"),
     Field("email","string"),
     Field("grad_year","integer"),
     Field("advisor_id", 'reference advisor'),
     Field('service_hours', 'integer', default=0),
     Field('registered','boolean',required=True),
     format='%(first_name)s %(last_name)s')
     
db.student.advisor_id.requires=IS_IN_DB(db,db.advisor.id,'%(first_name)s %(last_name)s')


#pulled from tracks
db.define_table("teacher",
     Field("first_name","string"),
     Field("last_name","string"),
     Field("email","string"),
     format='%(first_name)s %(last_name)s')


#pulled from tracks
db.define_table('chair',
                Field('first_name',required=True),
                Field('last_name',required=True),
                Field('email',required=True),
                format='%(first_name)s %(last_name)s')
 

db.chair.email.requires=IS_EMAIL()


#pulled from tracks
db.define_table('department',
                 Field('name',required=True),
                 Field('chair_id','reference chair', required=True),
                 format='%(name)s')
                      
db.department.chair_id.requires=IS_IN_DB(db,db.chair.id,'%(first_name)s %(last_name)s')

#pulled from tracks
db.define_table("course",
     Field("name","string"),
     Field("section","string"),
     Field("department_id","reference department"),
     Field("makes_rec","boolean"),
     format='%(name)s Section-%(section)s')

db.course.department_id.requires=IS_IN_DB(db,db.department.id,'%(name)s')

#pulled from tracks
db.define_table('student_course',
                Field('student_id','reference student', required=True),
                Field('course_id','reference course',required=True),
                format='%(student_id)s-%(course_id)s')

db.student_course.student_id.requires=IS_IN_DB(db,db.student.id,'%(first_name)s %(last_name)s')
db.student_course.course_id.requires=IS_IN_DB(db,db.course.id,'%(name)s Section-%(section)s')



#pulled from tracks
db.define_table('teacher_course',
                Field('teacher_id','reference teacher', required=True),
                Field('course_id','reference course',required=True),
                format='%(teacher_id)s-%(course_id)s')


db.teacher_course.teacher_id.requires=IS_IN_DB(db,db.teacher.id,'%(first_name)s %(last_name)s')
db.teacher_course.course_id.requires=IS_IN_DB(db,db.course.id,'%(name)s Section-%(section)s')

db.define_table('problem_type',
                Field('teacher_id','reference auth_user',required=True),
                Field('name','string',required=True),
                Field('given_list','text',required=True),
                Field('prompt','text',required=True),
                Field('sol_alg','text',required=True),
                format='%(name)s')

db.define_table('problem_type_given_type',
                Field('problem_type_id','reference problem_type',required=True),
                Field('name','string',required=True),
                Field('lower_bound','integer',default=1),
                Field('upper_bound','integer',default=20))

db.define_table('problem_type_course',
                Field('problem_type_id','reference problem_type',required=True),
                Field('course_id','reference course',required=True),
                )

db.define_table('problem',
                Field('user_id','reference auth_user',required=True),
                Field('problem_type_id','reference problem_type',required=True),
                Field('answered','boolean',default=False,required=True),
                Field('solution','decimal(2,10)',required=True),
                format='%(id)s')

db.define_table('problem_given',
                Field('given_type_id','reference problem_type_given_type',required = True),
                Field('given','integer',required=True),
                Field('problem_id','reference problem',required=False))
                #Field('problem_type_id','reference problem_type',required=False),
                #Field('user_id','reference auth_user',required=False))
                
                

#num_tries currently does not update in controller
db.define_table('user_score',
                Field('user_id','reference auth_user',required=True),
                Field('problem_type_id','reference problem_type',required=True),
                Field('num_tries','integer',required=True),
                Field('num_solved','integer',required=True))
