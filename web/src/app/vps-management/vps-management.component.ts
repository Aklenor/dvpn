import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { RequestsService } from '../requests.service';
import { vpsList } from '../vpsList';
import {animate, state, style, transition, trigger} from '@angular/animations';

@Component({
  selector: 'app-vps-management',
  templateUrl: './vps-management.component.html',
  styleUrls: ['./vps-management.component.css'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({height: '0px', minHeight: '0'})),
      state('expanded', style({height: '*'})),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],
})

export class VpsManagementComponent {

  vpsList: vpsList[];
  displayedColumns: string[] = ['hostname', 'interface', 'ip', 'location', 'route'];
  dataSource;

  constructor(private http: RequestsService) { }

  ngOnInit() {

    this.http.getVpsList().subscribe((data: vpsList[]) => {
      this.vpsList = data;
      this.dataSource = new MatTableDataSource(this.vpsList);
    }
    )
  }
  applyFilter(filterValue: string) {
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }
}