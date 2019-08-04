import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of, from } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { vpsList } from './vpsList'
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class RequestsService {

  constructor(private http: HttpClient) { }

  private url = environment.apiUrl;  // URL to web api

  getVpsList(): Observable<vpsList[]> {
    return this.http.get<vpsList[]>(`${this.url}\availablevps`);
  }

  getIpAddress(): Observable<any> {
    return this.http.get(`http://ip-api.com/json`);
  }

  addVPS(data: any): Observable<any> {
    return this.http.post(`${this.url}add_vps`, data);
  }

  addRoute(data: any): Observable<any> {
    return this.http.post(`${this.url}add_route`, data);
  }

  deleteVPS(data: any): Observable<any> {
    return this.http.post(`${this.url}del_vps`, data);
  }

  deleteRoute(data: any): Observable<any> {
    return this.http.post(`${this.url}del_route`, data);
  }
  getSSH(): Observable<any> {
    return this.http.get(`${this.url}getpubkey`);
  }

  getRoutes(): Observable<any> {
    return this.http.get(`${this.url}\getroutes`);
  }
}

