import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { VpsManagementComponent } from './vps-management.component';

describe('VpsManagementComponent', () => {
  let component: VpsManagementComponent;
  let fixture: ComponentFixture<VpsManagementComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ VpsManagementComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VpsManagementComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
