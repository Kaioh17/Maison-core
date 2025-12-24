


class ServiceContext:
    def __init__(self, db, current_user):
        """
        Docstring for __init__
        
        :param self: Description
        :param db: Description
        :param current_user: Description
        """
        self.db = db
        self.current_user=current_user
        if self.current_user:
            self.role = self.current_user.role.lower()
            if self.role != 'tenant': #not tenant
                self.tenant_id = self.current_user.tenant_id
                self.tenant_email = self.current_user.tenants.email
                self.full_name = self.current_user.full_name
                if self.role== 'driver':
                    self.driver_id = self.current_user.id
                    
                else:
                    self.rider_id = self.current_user.id
            else: # is tenant
                self.tenant_id = self.current_user.id
                self.tenant_email = self.current_user.email
                
# def get_service_(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
#     return BookingService(db = db, current_user=current_user)
# def get_unauthorized_booking_service(db = Depends(get_db)):
#     return BookingService(db = db)