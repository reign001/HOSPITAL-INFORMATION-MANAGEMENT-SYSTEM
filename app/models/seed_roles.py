def seed_roles():
    from app import db
    from app.models.employee import Role

    roles = {
    "SuperAdmin": "all",
    "Admin": "manage_users,view_patient,add_vitals,create_diagnosis,approve_lab,approve_medications,view_reports",
    "Doctor": "view_patient,create_diagnosis,request_lab,prescribe_medication,view_vitals",
    "Nurse": "view_patient,add_vitals,record_medication,view_lab_results",
    }


    for name, perms in roles.items():
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name, permissions=perms))
    db.session.commit()
    print("Roles created successfully!")
