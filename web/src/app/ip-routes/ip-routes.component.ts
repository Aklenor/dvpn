import { Component, OnInit } from '@angular/core';
import { RequestsService } from '../requests.service';
import { vpsList } from '../vpsList';

@Component({
  selector: 'app-ip-routes',
  templateUrl: './ip-routes.component.html',
  styleUrls: ['./ip-routes.component.css']
})
export class IpRoutesComponent implements OnInit {

  dataRoutes;
  isLoadingResults = true;

  constructor(private http: RequestsService) { }

  ngOnInit() {
    let arr = [];
    this.http.getVpsList().subscribe((data: vpsList[]) => {
      for (let el in data) {
        arr.push(data[el]);
      }
      this.dataRoutes = arr;
      console.log(this.dataRoutes);
      this.isLoadingResults = false;
    }
    )
  }

}
