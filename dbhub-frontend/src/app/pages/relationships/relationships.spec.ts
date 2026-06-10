import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Relationships } from './relationships';

describe('Relationships', () => {
  let component: Relationships;
  let fixture: ComponentFixture<Relationships>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Relationships],
    }).compileComponents();

    fixture = TestBed.createComponent(Relationships);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
