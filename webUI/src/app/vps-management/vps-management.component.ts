import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { RequestsService } from '../requests.service';
import { vpsList } from '../vpsList';

@Component({
  selector: 'app-vps-management',
  templateUrl: './vps-management.component.html',
  styleUrls: ['./vps-management.component.css']
})
export class VpsManagementComponent {

  vpsList: vpsList[];
  displayedColumns: string[] = ['name', 'interface', 'ip', 'city'];
  dataSource;

  constructor(private http: RequestsService) {}

  ngOnInit() {

    this.http.getVpsList().subscribe( (data: vpsList[]) => {
      this.vpsList = data;
      this.dataSource = new MatTableDataSource(this.vpsList);
      console.log(this.dataSource);
      console.log(this.vpsList);
    }
    )
  }

  applyFilter(filterValue: string) {
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }
}