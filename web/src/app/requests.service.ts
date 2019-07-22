import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of, from } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import {vpsList} from './vpsList'

@Injectable({
  providedIn: 'root'
})
export class RequestsService {

  constructor( private http: HttpClient) { }

  private url = 'http://127.0.0.1:5000/';  // URL to web api

  getVpsList (): Observable<vpsList[]> {
    return this.http.get<vpsList[]>(`${this.url}\availablevps`);
      // .pipe(
      //   catchError(this.handleError<any>('getVpsList', []))
      // );
  }

  getIpAddress (): Observable<any>{
    return this.http.get(`http://ip-api.com/json`);
  }

  chooseVPS(hostname): Observable<any>{
    return this.http.post(`${this.url}\chooseVPS`,hostname);
  }

}
