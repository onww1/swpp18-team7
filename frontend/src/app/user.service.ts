import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { HttpHeaders } from '@angular/common/http';

import { User } from './user';

@Injectable({
  providedIn: 'root'
})
export class UserService {

	userUrl = 'api/user';

	httpOptions = {
  headers: new HttpHeaders({
    'Content-Type':  'application/json',
    'Authorization': 'my-auth-token'
  });
  

  constructor(
  	private http: HttpClient
  	) { }

  authenticate(email: string, password: string) {
  	this.http.post<User>(this.userUrl, {"email": email, "password": password}).subscribe(
  		status => {
  			console.log(status);
  		});
  }

}
