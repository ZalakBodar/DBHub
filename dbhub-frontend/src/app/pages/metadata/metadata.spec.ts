import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Metadata } from './metadata';

describe('Metadata', () => {
  let component: Metadata;
  let fixture: ComponentFixture<Metadata>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Metadata],
    }).compileComponents();

    fixture = TestBed.createComponent(Metadata);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
