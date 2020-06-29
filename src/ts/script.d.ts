declare namespace ScoutId {
    interface loginResponse {
        admin: boolean;
        user: number | false;
    }

    interface jwtBadResponse {
        error: string;
        ok: false;
        url: string;
    }
    interface jwtGoodResponse {
        ok: true;
        token: string;
    }
    type jwtResponse = jwtGoodResponse|jwtBadResponse;

    interface stringObject {
        [key: string]: string;
    }

    interface jwtData {
        dob: string;
        email: string;
        exp: number;
        iat: number;
        iss: string;
        karer: stringObject;
        name: string;
        role: string[];
        sub: string;
    }
    interface whoamiResponse {
        admin: boolean;
        data: jwtData;
        error?: string;
        user: string|false;
    }
}
